"""admin-006 verification: deleting course material, and the term guard.

    .venv/Scripts/python.exe backend/scripts/verify_admin_006.py [base_url]

Creates its own throwaway course and materials so it never touches the demo
corpus, and cleans them up at the end.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

sys.path.insert(0, "backend")

from app.db import get_sessionmaker  # noqa: E402
from app.models import Chunk, Course, Material  # noqa: E402

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


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        _failures.append(label)


_, d = call("POST", "/auth/login",
            body={"email": "admin@example.edu", "password": "demo1234"})
admin = d["token"]

db = get_sessionmaker()()
today = date.today()

# A throwaway course, so nothing here can touch the demo corpus.
course = db.scalar(
    __import__("sqlalchemy").select(Course).where(Course.code == "ZZTEST"))
if course is None:
    course = Course(code="ZZTEST", title="Throwaway Test Course")
    db.add(course)
db.commit()


def make_material(title, *, ingested: bool) -> int:
    m = Material(course_id=course.id, title=title, kind="notes",
                 status="active", ingest_status="complete" if ingested else "queued")
    db.add(m)
    db.flush()
    if ingested:
        db.add(Chunk(material_id=m.id, page_no=1, text="throwaway",
                     char_start=0, char_end=9, embedding=[0.0] * 384))
    db.commit()
    return m.id


def set_term(start, end):
    st, _ = call("PUT", f"/admin/courses/{course.id}/term", admin,
                 {"term_start": start.isoformat() if start else None,
                  "term_end": end.isoformat() if end else None})
    return st


print("=" * 74)
print("[1] never-ingested material deletes freely, even mid-term")
print("=" * 74)
set_term(today - timedelta(days=30), today + timedelta(days=30))
mid = make_material("never ingested", ingested=False)
st, body = call("DELETE", f"/admin/materials/{mid}", admin)
print(f"  DELETE -> HTTP {st}")
check("204 for material that was never ingested", st == 204)
db.expire_all()
check("the row is gone", db.get(Material, mid) is None)

print()
print("=" * 74)
print("[2] ingested material, course mid-term -> 409 mid_term")
print("=" * 74)
mid = make_material("ingested, mid-term", ingested=True)
st, body = call("DELETE", f"/admin/materials/{mid}", admin)
print(f"  DELETE -> HTTP {st}")
print(f"  {json.dumps(body, indent=2)[:400]}")
check("409", st == 409)
check("code is mid_term", (body or {}).get("error", {}).get("code") == "mid_term")
check("it says what to do instead",
      "archive" in (body or {}).get("error", {}).get("message", "").lower())
check("it names the window and the size",
      set((body or {}).get("error", {}).get("detail", {})) >=
      {"course", "term_start", "term_end", "chunk_count"})
db.expire_all()
check("the material survived the refusal", db.get(Material, mid) is not None)

print()
print("=" * 74)
print("[3] same material, course now OUTSIDE its term -> 204")
print("=" * 74)
set_term(today - timedelta(days=200), today - timedelta(days=100))
st, _ = call("DELETE", f"/admin/materials/{mid}", admin)
print(f"  DELETE -> HTTP {st}")
check("204 once the term is over", st == 204)
db.expire_all()
check("material gone", db.get(Material, mid) is None)
check("its chunks cascaded",
      db.query(Chunk).filter(Chunk.material_id == mid).count() == 0)

print()
print("=" * 74)
print("[4] a course with NO term dates has no protected window")
print("=" * 74)
set_term(None, None)
mid = make_material("ingested, no dates", ingested=True)
st, _ = call("DELETE", f"/admin/materials/{mid}", admin)
print(f"  DELETE -> HTTP {st}")
check("204 -- an unrecorded term must not freeze an admin out", st == 204)

print()
print("=" * 74)
print("[5] the audit row outlives the material, and reads as a sentence")
print("=" * 74)
_, log = call("GET", "/admin/audit-log?action=material.delete&limit=3", admin)
for r in log["items"][:3]:
    print(f"  - {r['summary']}")
check("a material.delete row exists", log["total"] > 0)
check("it survived the material it describes",
      any("material" in (r.get("target") or "") for r in log["items"]))

print()
print("=" * 74)
print("[6] unknown material is 404, and archiving still works")
print("=" * 74)
st, _ = call("DELETE", "/admin/materials/999999", admin)
print(f"  DELETE unknown -> HTTP {st}")
check("404", st == 404)
mid = make_material("to be archived", ingested=True)
st, body = call("POST", f"/admin/materials/{mid}/archive", admin)
print(f"  archive -> HTTP {st}, status={(body or {}).get('status')}")
check("archive still returns 200 archived",
      st == 200 and body.get("status") == "archived")

# cleanup
for m in db.query(Material).filter(Material.course_id == course.id).all():
    db.delete(m)
db.delete(course)
db.commit()
print("\n  (throwaway course and materials cleaned up)")

print()
print("=" * 74)
print(f"{len(_failures)} failure(s)" if _failures else "ALL CHECKS PASSED")
for f in _failures:
    print("  FAILED:", f)
print("=" * 74)
sys.exit(1 if _failures else 0)
