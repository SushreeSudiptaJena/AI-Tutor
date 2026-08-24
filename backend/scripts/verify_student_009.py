"""student-009 verification: answers survive a reload.

Runs the `verification` steps from feature_list.json verbatim against a live
backend and prints what actually came back. Usage:

    .venv/Scripts/python.exe backend/scripts/verify_student_009.py [base_url]

Read-only apart from the diagnostic submit and one practice answer, both of
which are the thing under test. Run `reset_demo_state.py` afterwards to put the
demo back to its scripted starting point.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
STUDENT = ("asha@example.edu", "demo1234")
OTHER = ("ravi@example.edu", "demo1234")

_failures: list[str] = []


def call(method: str, path: str, token: str | None = None, body: dict | None = None):
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


def login(creds) -> str:
    _, d = call("POST", "/auth/login", body={"email": creds[0], "password": creds[1]})
    return d["token"]


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        _failures.append(label)


tok = login(STUDENT)

print("=" * 74)
print("[1] GET /student/diagnostic before submitting")
print("=" * 74)
_, diag = call("GET", "/student/diagnostic", tok)
did = diag["diagnostic_id"]
print(f"  diagnostic_id = {did}   submitted_at = {diag['submitted_at']!r}")
check("no item leaks correct_answer", not any("correct_answer" in i for i in diag["items"]))
print(f"  (this student has already submitted, so your_answer is populated below)")

print()
print("=" * 74)
print("[2] submit 5 of 8 answers, then read them back")
print("=" * 74)
answers = [
    (121, "`pip freeze` lists only what is installed in the active environment"),
    (122, "They are set to None"),
    (123, "The page they came from"),
    (124, "GET, because it is a simpler request"),
    (126, "A stable auto-generated id"),
]
sent = {i: a for i, a in answers}
st, res = call("POST", f"/student/diagnostic/{did}/submit", tok,
               {"answers": [{"item_id": i, "answer": a} for i, a in answers]})
print(f"  submit -> HTTP {st}: {res['message']}")
check("no score key in the submit response",
      set(res) == {"gaps", "message"}, f"keys = {sorted(res)}")

_, diag = call("GET", "/student/diagnostic", tok)
print(f"  submitted_at = {diag['submitted_at']}")
for it in diag["items"]:
    print(f"    item {it['id']}  your_answer = {it['your_answer']!r}")
check("every answered item replays the exact string that was sent",
      all(it["your_answer"] == sent[it["id"]] for it in diag["items"] if it["id"] in sent))
check("items never answered stay null",
      all(it["your_answer"] is None for it in diag["items"] if it["id"] not in sent))
check("submitted_at is set", diag["submitted_at"] is not None)
check("correct_answer still absent", not any("correct_answer" in i for i in diag["items"]))

print()
print("=" * 74)
print("[3] re-submitting one item overwrites rather than duplicating")
print("=" * 74)
call("POST", f"/student/diagnostic/{did}/submit", tok,
     {"answers": [{"item_id": 124, "answer": "Either one; the method makes no difference"}]})
_, diag = call("GET", "/student/diagnostic", tok)
now = next(i["your_answer"] for i in diag["items"] if i["id"] == 124)
print(f"    item 124 your_answer = {now!r}")
check("item 124 shows the newer answer", now == "Either one; the method makes no difference")
call("POST", f"/student/diagnostic/{did}/submit", tok,
     {"answers": [{"item_id": 124, "answer": sent[124]}]})
_, diag = call("GET", "/student/diagnostic", tok)
back = next(i["your_answer"] for i in diag["items"] if i["id"] == 124)
print(f"    restored to  {back!r}")
check("one row per item, always the latest", back == sent[124])

print()
print("=" * 74)
print("[4] correctness is not stored for diagnostic items at all")
print("=" * 74)
sys.path.insert(0, "backend")
from sqlalchemy import inspect  # noqa: E402
from app.db import get_engine  # noqa: E402

cols = [c["name"] for c in inspect(get_engine()).get_columns("diagnostic_responses")]
print(f"  diagnostic_responses columns: {cols}")
check("no correctness/score column exists",
      not any(c in ("correct", "is_correct", "score", "grade") for c in cols))

print()
print("=" * 74)
print("[5] a freshly generated practice set has nothing answered")
print("=" * 74)
_, gaps = call("GET", "/student/gaps", tok)
gap = next(g for g in gaps["items"] if g["concept"].startswith("HTTP methods"))
_, gen = call("POST", "/student/practice/generate", tok, {"gap_id": gap["id"]})
new_set = gen["practice_set_id"]
_, fresh = call("GET", f"/student/practice/{new_set}", tok)
print(f"  set {fresh['practice_set_id']} | concept: {fresh['concept']} | source: {fresh['source']}")
for it in fresh["items"]:
    print(f"    item {it['id']} your_answer={it['your_answer']!r} "
          f"correct={it['correct']!r} diagnosis={it['diagnosis']!r}")
check("unanswered items have your_answer, correct and diagnosis all null",
      all(i["your_answer"] is None and i["correct"] is None and i["diagnosis"] is None
          for i in fresh["items"]))
check("GET echoes generate's shape",
      set(fresh) == {"practice_set_id", "concept", "source", "items"},
      f"keys = {sorted(fresh)}")
check("no correct_answer in the set", not any("correct_answer" in i for i in fresh["items"]))

print()
print("=" * 74)
print("[6] answer one wrong -> the pending diagnosis comes back on re-read")
print("=" * 74)
target = fresh["items"][0]["id"]
_, ans = call("POST", f"/student/practice/{new_set}/answer", tok,
              {"item_id": target, "answer": "GET"})
d = ans["diagnosis"] or {}
print(f"  POST answer -> correct={ans['correct']} diagnosis id={d.get('id')} "
      f"label={d.get('label')!r}")
_, again = call("GET", f"/student/practice/{new_set}", tok)
it = next(i for i in again["items"] if i["id"] == target)
print(f"  GET  item {target} your_answer={it['your_answer']!r} correct={it['correct']!r}")
print(f"  GET  diagnosis = {json.dumps(it['diagnosis'])}")
check("your_answer and correct replay the attempt",
      it["your_answer"] == "GET" and it["correct"] is False)
check("the same diagnosis comes back", it["diagnosis"] and it["diagnosis"]["id"] == d.get("id"))
check("it is still pending (confirmed null)", it["diagnosis"]["confirmed"] is None)
check("explanation is NOT replayed", "explanation" not in it)
check("citations are NOT replayed", "citations" not in it)

print()
print("=" * 74)
print("[7] confirming flips confirmed to true; the GET itself confirms nothing")
print("=" * 74)
_, heat_before = call("GET", "/teacher/misconceptions/heatmap", login(OTHER))
call("GET", f"/student/practice/{new_set}", tok)          # a read must not count
_, heat_after_read = call("GET", "/teacher/misconceptions/heatmap", login(OTHER))
check("reading the set left the heatmap unchanged",
      heat_before["items"] == heat_after_read["items"])

st, _ = call("POST", f"/student/misconception-diagnosis/{it['diagnosis']['id']}/confirm",
             tok, {"confirmed": True})
print(f"  confirm -> HTTP {st}")
_, after = call("GET", f"/student/practice/{new_set}", tok)
conf = next(i for i in after["items"] if i["id"] == target)["diagnosis"]["confirmed"]
print(f"  confirmed now = {conf}")
check("confirmed is true after confirming", conf is True)

print()
print("=" * 74)
print("[8] another student's set is 404, not 403")
print("=" * 74)
st, body = call("GET", f"/student/practice/{new_set}", login(OTHER))
print(f"  HTTP {st}: {json.dumps(body)}")
check("404 not_found", st == 404 and body["error"]["code"] == "not_found")

print()
print("=" * 74)
print("[9] gaps carry latest_practice_set_id")
print("=" * 74)
_, gaps = call("GET", "/student/gaps", tok)
for g in gaps["items"]:
    print(f"  gap {g['id']:<5} {g['concept']:<42} latest_practice_set_id={g['latest_practice_set_id']}")
check("the gap just practised points at the newest set",
      next(g["latest_practice_set_id"] for g in gaps["items"] if g["id"] == gap["id"]) == new_set)

print()
print("=" * 74)
print(f"{len(_failures)} failure(s)" if _failures else "ALL CHECKS PASSED")
for f in _failures:
    print("  FAILED:", f)
print("=" * 74)
sys.exit(1 if _failures else 0)
