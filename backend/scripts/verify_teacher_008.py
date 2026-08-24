"""teacher-008 verification: reteach drafts from both rankings.

    .venv/Scripts/python.exe backend/scripts/verify_teacher_008.py [base_url]

Runs the feature_list.json verification steps against a live backend.
Mutates state (creates draft reteach units). Run reset_demo_state.py after.
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


teacher = login("ravi@example.edu")
student = login("asha@example.edu")

print("=" * 76)
print("the two rankings this draws from")
print("=" * 76)
_, heat = call("GET", "/teacher/misconceptions/heatmap", teacher)
_, gaps = call("GET", "/teacher/gap-map", teacher)
print("  heatmap top 3:")
for r in heat["items"][:3]:
    print(f"    #{r['misconception_id']:<4} {r['confirmed_count']:>3} confirmed  {r['label'][:56]}")
print("  gap map top 3:")
for r in gaps["items"][:3]:
    print(f"    #{r['concept_id']:<4} {r['students_missing']:>3} missing    {r['concept'][:56]}")

print()
print("=" * 76)
print("[1] POST /teacher/reteach/suggest-top")
print("=" * 76)
_, before_assign = call("GET", "/student/assignments", student)
st, res = call("POST", "/teacher/reteach/suggest-top", teacher)
print(f"  HTTP {st}   created {len(res['created'])}, skipped {len(res['skipped'])}")
for u in res["created"]:
    print(f"    created  unit {u['id']:<4} target={u['target']:<13} {u['title'][:48]}")
for s in res["skipped"]:
    extra = f" ({s.get('alignment_percent')}%)" if "alignment_percent" in s else ""
    print(f"    skipped  {s['target']:<13} {s['reason']:<24}{extra} {s['label'][:38]}")
check("returns 200, not 201 -- it is a partial-success report", st == 200)
cov = res["coverage"]
print(f"  coverage: {cov['from_heatmap']}/{cov['requested_per_ranking']} from the heatmap, "
      f"{cov['from_gap_map']}/{cov['requested_per_ranking']} from the gap map")
check("it drew on both rankings",
      cov["from_heatmap"] > 0 and cov["from_gap_map"] > 0, str(cov))
check("it filled the panel rather than stopping at the literal top three",
      cov["from_heatmap"] + cov["from_gap_map"] >= 5, str(cov))

print()
print("=" * 76)
print("[2] exactly one target is set on every unit")
print("=" * 76)
_, listing = call("GET", "/teacher/reteach?status=draft", teacher)
kinds = {}
for u in listing["items"]:
    one = (u["misconception_id"] is None) != (u["concept_id"] is None)
    kinds[u["target"]] = kinds.get(u["target"], 0) + 1
    if not one:
        check(f"unit {u['id']} has exactly one target", False)
print(f"  draft units by target: {kinds}")
check("every unit has exactly one target set",
      all((u["misconception_id"] is None) != (u["concept_id"] is None)
          for u in listing["items"]))
check("both kinds exist", kinds.get("misconception", 0) > 0 and kinds.get("concept", 0) > 0,
      str(kinds))
for u in listing["items"]:
    if u["target"] == "concept":
        check("a concept unit carries no practice items (no error pattern yet)",
              u["practice_items"] == [])
        break

print()
print("=" * 76)
print("[3] nothing was assigned")
print("=" * 76)
statuses = {u["status"] for u in res["created"]}
print(f"  statuses of created units: {statuses or '(none created)'}")
_, after_assign = call("GET", "/student/assignments", student)
check("everything created is a draft", statuses <= {"draft"})
check("GET /student/assignments is unchanged",
      before_assign["items"] == after_assign["items"],
      f"{len(before_assign['items'])} -> {len(after_assign['items'])}")

print()
print("=" * 76)
print("[4] a refusal skips one target, it does not fail the batch")
print("=" * 76)
refused = [s for s in res["skipped"] if s["reason"] == "insufficient_evidence"]
if refused:
    for s in refused:
        print(f"  refused: {s['label'][:52]} at {s.get('alignment_percent')}%")
    check("a refusal is reported as a skip and the batch still returned 200",
          st == 200)
else:
    print("  (no target refused this run -- the corpus supported all six)")
check("no skip reason is an unhandled error",
      all(s["reason"] in {"insufficient_evidence", "already_drafted",
                          "already_assigned", "covered_by_misconception",
                          "provider_unavailable"} for s in res["skipped"]),
      str({s["reason"] for s in res["skipped"]}))

print()
print("=" * 76)
print("[5] running it again does not duplicate")
print("=" * 76)
n_before = len(call("GET", "/teacher/reteach?status=draft", teacher)[1]["items"])
_, again = call("POST", "/teacher/reteach/suggest-top", teacher)
n_after = len(call("GET", "/teacher/reteach?status=draft", teacher)[1]["items"])
print(f"  draft units {n_before} -> {n_after}; second run created "
      f"{len(again['created'])}, skipped {len(again['skipped'])}")
for s in again["skipped"][:6]:
    print(f"    {s['target']:<13} {s['reason']}")
check("no new units on a second run", n_after == n_before)
check("the existing drafts are reported as already_drafted",
      any(s["reason"] == "already_drafted" for s in again["skipped"]))

print()
print("=" * 76)
print("[6] overlap between the two rankings is reported, not duplicated")
print("=" * 76)
overlap = [s for s in res["skipped"] + again["skipped"]
           if s["reason"] == "covered_by_misconception"]
if overlap:
    for s in overlap:
        print(f"  {s['label'][:50]} -> already covered by unit {s['unit_id']}")
else:
    print("  (no overlap this run)")
titles = [u["title"] for u in listing["items"]]
check("no two draft units share a title", len(titles) == len(set(titles)))

print()
print("=" * 76)
print("[7] single suggest still works, both ways, and rejects ambiguity")
print("=" * 76)
mid = heat["items"][0]["misconception_id"]
cid = gaps["items"][0]["concept_id"]
st1, u1 = call("POST", "/teacher/reteach/suggest", teacher, {"misconception_id": mid})
print(f"  {{misconception_id}} -> HTTP {st1} target={u1.get('target')}")
check("misconception_id still works", st1 in (200, 201, 422))
st2, u2 = call("POST", "/teacher/reteach/suggest", teacher, {"concept_id": cid})
print(f"  {{concept_id}}        -> HTTP {st2} target={u2.get('target')}")
check("concept_id works", st2 in (200, 201, 422))
for bad in ({}, {"misconception_id": mid, "concept_id": cid}):
    stb, _ = call("POST", "/teacher/reteach/suggest", teacher, bad)
    print(f"  {json.dumps(bad):<44} -> HTTP {stb}")
    check(f"{bad or 'empty body'} is a 422", stb == 422)

print()
print("=" * 76)
print(f"{len(_failures)} failure(s)" if _failures else "ALL CHECKS PASSED")
for f in _failures:
    print("  FAILED:", f)
print("=" * 76)
sys.exit(1 if _failures else 0)
