"""The golden path, end to end, against a live backend.

    .venv/Scripts/python.exe backend/scripts/smoke_golden_path.py [base_url]

diagnostic -> gap attributed to the prerequisite course -> lesson with an
alignment score and page citations -> scoped practice -> wrong answer -> a
specific misconception -> confirm -> the teacher heatmap increments.

Mutates demo state. Run `reset_demo_state.py` afterwards.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
_failures: list[str] = []


def call(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return e.code, (json.loads(raw) if raw else None)


def login(email):
    _, d = call("POST", "/auth/login", body={"email": email, "password": "demo1234"})
    return d["token"]


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        _failures.append(label)


student = login("asha@example.edu")
teacher = login("ravi@example.edu")

print("1. diagnostic -- answer the HTTP-methods item wrong, as the demo script does")
_, diag = call("GET", "/student/diagnostic", student)
http_item = next(i for i in diag["items"] if i["concept"].startswith("HTTP methods"))
wrong = next(o for o in http_item["options"] if o.startswith("GET, because"))
_, res = call("POST", f"/student/diagnostic/{diag['diagnostic_id']}/submit", student,
              {"answers": [{"item_id": http_item["id"], "answer": wrong}]})
print(f"   {res['message']}")
check("no score in the submit response", set(res) == {"gaps", "message"})

gap = next((g for g in res["gaps"] if g["concept"].startswith("HTTP methods")), None)
check("a gap was raised for the missed concept", gap is not None)
print(f"   gap {gap['id']} <- {gap['prerequisite_course']}")
check("the gap is attributed to the prerequisite course",
      gap["prerequisite_course"] == "Computer Science Workshop 1")

print("2. the answer survives a reload (student-009)")
_, again = call("GET", "/student/diagnostic", student)
replayed = next(i["your_answer"] for i in again["items"] if i["id"] == http_item["id"])
check("the picked option comes back", replayed == wrong)

print("3. lesson")
_, lesson = call("GET", f"/student/gaps/{gap['id']}/lesson", student)
ev = lesson["evidence"]
print(f"   outcome={lesson['outcome']} alignment={ev['alignment_percent']}% "
      f"top-sim={ev['top_similarity']} citations={len(lesson['citations'])}")
check("the lesson was answered, not refused", lesson["outcome"] == "answered")
check("it carries real page citations",
      bool(lesson["citations"]) and all(c["page_no"] for c in lesson["citations"]))
check("read-aloud text is present", bool(lesson.get("speech_text")))

print("4. practice scoped to that gap")
_, pset = call("POST", "/student/practice/generate", student, {"gap_id": gap["id"]})
print(f"   set {pset['practice_set_id']} | {pset['concept']} | {pset['source']} "
      f"| {len(pset['items'])} items")
check("practice is scoped to the gap's concept",
      pset["concept"].startswith("HTTP methods"))

print("5. answer one wrong -> a specific misconception")
item = pset["items"][0]
_, ans = call("POST", f"/student/practice/{pset['practice_set_id']}/answer", student,
              {"item_id": item["id"], "answer": "GET"})
d = ans["diagnosis"]
print(f"   correct={ans['correct']} diagnosis={d and d['label']!r}")
check("the wrong answer is diagnosed", d is not None)
check("the diagnosis is specific, not generic",
      d and "GET" in d["label"])

print("6. confirm -> the heatmap moves")
_, before = call("GET", "/teacher/misconceptions/heatmap", teacher)


def row_for(payload, mid):
    return next((r for r in payload["items"] if r.get("misconception_id") == mid), None)


b = row_for(before, d["misconception_id"])
call("POST", f"/student/misconception-diagnosis/{d['id']}/confirm", student,
     {"confirmed": True})
_, after = call("GET", "/teacher/misconceptions/heatmap", teacher)
a = row_for(after, d["misconception_id"])
bc = b["confirmed_count"] if b else 0
ac = a["confirmed_count"] if a else 0
print(f"   confirmed_count {bc} -> {ac}")
check("confirming increments the heatmap", ac == bc + 1)

print("7. the pending question survives a reload too (student-009)")
_, resumed = call("GET", f"/student/practice/{pset['practice_set_id']}", student)
ri = next(i for i in resumed["items"] if i["id"] == item["id"])
print(f"   your_answer={ri['your_answer']!r} correct={ri['correct']} "
      f"confirmed={ri['diagnosis'] and ri['diagnosis']['confirmed']}")
check("the answer and its confirmed diagnosis come back",
      ri["your_answer"] == "GET" and ri["diagnosis"]["confirmed"] is True)

print()
print(f"{len(_failures)} failure(s)" if _failures else "GOLDEN PATH INTACT")
for f in _failures:
    print("  FAILED:", f)
sys.exit(1 if _failures else 0)
