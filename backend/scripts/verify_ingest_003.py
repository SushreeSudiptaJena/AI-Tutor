"""ingest-003 verification: a half-ingested book must be invisible.

    .venv/Scripts/python.exe backend/scripts/verify_ingest_003.py

Builds a throwaway course with a deliberately half-written material, proves it
cannot be retrieved or advertised, then proves --doctor finds and clears it.
Cleans up after itself.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "backend")

from sqlalchemy import delete, func, select  # noqa: E402

from app.db import get_sessionmaker  # noqa: E402
from app.models import Chunk, Course, Material  # noqa: E402
from app.services import retrieval  # noqa: E402
from app.services.embed import embed_documents  # noqa: E402

_failures: list[str] = []


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        _failures.append(label)


db = get_sessionmaker()()

TEXT = ("A full adder adds three bits: two operands and a carry in. It produces "
        "a sum bit and a carry out, and chaining them gives a ripple carry adder.")

course = db.scalar(select(Course).where(Course.code == "ZZING"))
if course is None:
    course = Course(code="ZZING", title="Throwaway Ingest Course")
    db.add(course)
db.commit()

# Clean slate
for m in db.scalars(select(Material).where(Material.course_id == course.id)).all():
    db.execute(delete(Chunk).where(Chunk.material_id == m.id))
    db.delete(m)
db.commit()

print("=" * 74)
print("[1] a material mid-ingest: real chunks, ingest_status='running'")
print("=" * 74)
partial = Material(course_id=course.id, title="Half-written Logic Book",
                   kind="textbook", status="active",
                   ingest_status="running", chunk_count=0, page_count=800)
db.add(partial)
db.flush()
db.add(Chunk(material_id=partial.id, page_no=130, text=TEXT,
             char_start=0, char_end=len(TEXT),
             embedding=embed_documents([TEXT])[0]))
db.commit()
n = int(db.scalar(select(func.count()).select_from(Chunk)
                  .where(Chunk.material_id == partial.id)) or 0)
print(f"  material {partial.id}: status={partial.status!r} "
      f"ingest_status={partial.ingest_status!r} chunks={n} chunk_count={partial.chunk_count}")
check("it is 'active' -- so a status-only filter would serve it", partial.status == "active")
check("its chunks really are in the database", n == 1)

print()
print("=" * 74)
print("[2] retrieval must not return it")
print("=" * 74)
hits = retrieval.search(db, "What is a full adder?", course_id=course.id, k=5)
print(f"  retrieval.search -> {len(hits)} hits")
check("a half-ingested book is not retrievable", len(hits) == 0)

hits_arch = retrieval.search(db, "What is a full adder?", course_id=course.id,
                             k=5, include_archived=True)
print(f"  include_archived=True -> {len(hits_arch)} hits")
check("include_archived does not re-admit it either", len(hits_arch) == 0)

print()
print("=" * 74)
print("[3] once complete, the SAME material is retrievable")
print("=" * 74)
partial.ingest_status = "complete"
partial.chunk_count = 1
db.commit()
hits = retrieval.search(db, "What is a full adder?", course_id=course.id, k=5)
print(f"  retrieval.search -> {len(hits)} hits")
check("the guard is about completeness, not about hiding everything", len(hits) == 1)
if hits:
    print(f"    p.{hits[0].page_no} sim={hits[0].similarity:.3f} {hits[0].book_title}")

print()
print("=" * 74)
print("[4] --doctor finds an unfinished ingest and a chunk_count that drifted")
print("=" * 74)
partial.ingest_status = "running"       # back to unfinished
partial.chunk_count = 0
drifted = Material(course_id=course.id, title="Count Drifted", kind="notes",
                   status="active", ingest_status="complete", chunk_count=99)
db.add(drifted)
db.flush()
db.add(Chunk(material_id=drifted.id, page_no=1, text=TEXT, char_start=0,
             char_end=len(TEXT), embedding=embed_documents([TEXT])[0]))
db.commit()


class _Args:
    fix = False


sys.path.insert(0, "backend/scripts")
import ingest_pdfs  # noqa: E402

print("  --doctor (report only):")
ingest_pdfs.cmd_doctor(db, _Args())
db.expire_all()
still_there = db.get(Material, partial.id) is not None
check("reporting changes nothing", still_there)

print()
print("  --doctor --fix:")
_Args.fix = True
ingest_pdfs.cmd_doctor(db, _Args())
db.expire_all()
check("the unfinished material is gone", db.get(Material, partial.id) is None)
check("its partial chunks went with it",
      int(db.scalar(select(func.count()).select_from(Chunk)
                    .where(Chunk.material_id == partial.id)) or 0) == 0)
fixed = db.get(Material, drifted.id)
check("the drifted chunk_count was corrected, not deleted",
      fixed is not None and fixed.chunk_count == 1,
      f"chunk_count={fixed.chunk_count if fixed else None}")

# cleanup
for m in db.scalars(select(Material).where(Material.course_id == course.id)).all():
    db.execute(delete(Chunk).where(Chunk.material_id == m.id))
    db.delete(m)
db.delete(course)
db.commit()
print("\n  (throwaway course cleaned up)")

print()
print("=" * 74)
print(f"{len(_failures)} failure(s)" if _failures else "ALL CHECKS PASSED")
for f in _failures:
    print("  FAILED:", f)
print("=" * 74)
sys.exit(1 if _failures else 0)
