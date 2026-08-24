"""ingest-001 -- put the PDFs in backend/data/pdfs/ and run this.

    .venv/Scripts/python.exe backend/scripts/ingest_pdfs.py

CONTENT LEAD: that is the whole workflow. Drop the files in the folder and run
the line above. Editing manifest.json is optional -- it only exists so a file
called `hcv1.pdf` can display as "Concepts of Physics, Vol 1" and so a problem
set can be marked `kind: "assignment"`, which is what the graded-work guardrail
matches against. Anything not listed in the manifest is ingested as a textbook
titled after its filename.

Flags:
    --dir PATH        folder of PDFs/EPUBs       (default backend/data/pdfs)
    --file PATH       ingest one file only
    --title TEXT      title for --file           (default: the filename)
    --kind KIND       syllabus|textbook|notes|assignment  (default textbook)
    --course CODE     course code                (default: the seeded primary)
    --course-title T  create that course if the code is unknown
    --department NAME department for a course created that way
    --dry-run         parse and report; write nothing
    --verify          re-check chunks already in the database against the PDFs
    --sample N        chunks to verify per material  (default 3)

Runs on Sushree's machine only -- everyone else consumes the shared Neon rows.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# A Windows console is cp1252 and real books are not. Printing a chunk preview
# containing a typographic dash or a ligature would otherwise kill an ingest run
# that had already succeeded -- the progress output must never be the thing that
# fails.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models import Course, Department, Material, User
from app.services import ingest

PDF_DIR = Path(__file__).resolve().parents[1] / "data" / "pdfs"
SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"
MANIFEST = "manifest.json"


# ---------------------------------------------------------------------------
# What to ingest
# ---------------------------------------------------------------------------

def _is_converted_twin(path: Path, pdf_dir: Path) -> bool:
    """True for a .pdf we produced from an .epub in the same folder -- otherwise
    the book would be ingested twice, once per format."""
    if path.suffix.lower() != ".pdf":
        return False
    return any((pdf_dir / f"{path.stem}{suffix}").exists()
               for suffix in ingest.REFLOWABLE_SUFFIXES)


def plan_from_dir(pdf_dir: Path) -> list[dict]:
    """One entry per PDF. The manifest overrides title/kind where it names a file."""
    suffixes = {".pdf", *ingest.REFLOWABLE_SUFFIXES}
    files = sorted(p for p in pdf_dir.iterdir()
                   if p.is_file() and p.suffix.lower() in suffixes
                   and not _is_converted_twin(p, pdf_dir))
    overrides: dict[str, dict] = {}

    manifest_path = pdf_dir / MANIFEST
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in data.get("files", []):
            overrides[entry["file"]] = entry
        missing = [f for f in overrides if not (pdf_dir / f).exists()]
        for f in missing:
            print(f"  ! manifest lists {f}, which is not in {pdf_dir.name}/ -- skipped")

    plan = []
    for path in files:
        entry = overrides.get(path.name, {})
        plan.append({
            "path": path,
            "title": entry.get("title") or path.stem.replace("_", " ").replace("-", " ").strip(),
            "kind": entry.get("kind", "textbook"),
            "course": entry.get("course"),
        })
    return plan


def resolve_course(db, code: str | None, title: str | None = None,
                   department: str | None = None) -> Course:
    """Find the course, or create it when --course-title says to.

    Creating one here is deliberate: material has to belong to a course before
    it can be ingested, and retrieval is course-scoped, so a book filed under
    the wrong course is invisible rather than merely untidy.
    """
    if code:
        course = db.scalar(select(Course).where(Course.code == code))
        if course is not None:
            return course
        if not title:
            sys.exit(f"No course with code {code!r}. Run seed.py first, or pass "
                     f"--course-title to create it.")
        dept = None
        if department:
            dept = db.scalar(select(Department).where(Department.name == department))
            if dept is None:
                dept = Department(name=department)
                db.add(dept)
                db.flush()
        course = Course(code=code, title=title,
                        department_id=dept.id if dept else None)
        db.add(course)
        db.flush()
        print(f"  created course {code} - {title}"
              + (f" ({department})" if department else ""))
        return course

    primary = json.loads((SEED_DIR / "course.json").read_text(encoding="utf-8"))["primary_course"]
    course = db.scalar(select(Course).where(Course.code == primary))
    if course is None:
        sys.exit(f"Primary course {primary!r} is not in the database. Run seed.py first.")
    return course


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def do_dry_run(plan: list[dict]) -> None:
    print("\nDRY RUN -- parsing only, nothing is written.\n")
    for item in plan:
        pdf, converted = ingest.ensure_fixed_pdf(item["path"], item["path"].parent)
        if converted:
            print(f"  laid out {item['path'].name} -> {pdf.name} "
                  f"(A4 / {ingest.LAYOUT_FONTSIZE}pt)")
        parsed = ingest.parse_pdf(pdf)
        print(f"  {item['path'].name}")
        print(f"    title   {item['title']}")
        print(f"    kind    {item['kind']}")
        print(f"    pages   {parsed.page_count} ({parsed.pages_with_text} with text)")
        print(f"    chunks  {parsed.chunk_count}")
        if parsed.chunks:
            first = parsed.chunks[0]
            print(f"    p.{first.page_no} [{first.char_start}:{first.char_end}] "
                  f"{' '.join(first.text.split())[:70]}...")
        if parsed.pages_with_text == 0:
            print("    ! no text layer at all -- this is a scanned PDF; OCR is out of scope")
        print()


def do_ingest(db, plan: list[dict], default_course: Course, args) -> None:
    admin = db.scalar(select(User).where(User.role == "admin"))

    for item in plan:
        course = resolve_course(db, item["course"]) if item["course"] else default_course
        print(f"\n  {item['path'].name}  ->  {course.code}  ({item['kind']})")

        pdf, converted = ingest.ensure_fixed_pdf(item["path"], item["path"].parent)
        if converted:
            print(f"    reflowable source laid out to {pdf.name} at A4 / "
                  f"{ingest.LAYOUT_FONTSIZE}pt -- page numbers are this "
                  f"rendering's, not the printed book's")

        def progress(phase: str, done: int, total: int) -> None:
            print(f"    {phase} {done}/{total}   ", end="\r", flush=True)

        result = ingest.ingest_material(
            db,
            course_id=course.id,
            title=item["title"],
            kind=item["kind"],
            path=pdf,
            uploaded_by_id=admin.id if admin else None,
            progress=progress,
        )
        print(" " * 44, end="\r")     # clear the progress line

        note = f"  (replaced {result.replaced} existing chunks)" if result.replaced else ""
        print(f"    {result.title[:50]:52} {result.chunk_count:5} chunks from "
              f"{result.pages_with_text}/{result.page_count} pages{note}")

        checks = ingest.verify_material(db, result.material_id, pdf, sample=args.sample)
        report_checks(checks)

    stubs = ingest.stub_corpus_materials(db, default_course.id)
    if stubs:
        print("\n  ! The stand-in corpus is still loaded in this course, alongside "
              "the real material:")
        for title in stubs:
            print(f"      {title}")
        print("    Placeholder passages compete with the real book in search results.")
        print("    Set \"enabled\": false in backend/data/seed/corpus.json and re-run")
        print("    seed.py, then re-run backend/scripts/calibrate_threshold.py --")
        print("    the refusal threshold is corpus-specific and will have moved.")


def do_verify(db, plan: list[dict], args) -> int:
    """Re-check stored chunks against the PDFs. Exit code is the failure count."""
    by_name = {}
    for item in plan:
        pdf, _ = ingest.ensure_fixed_pdf(item["path"], item["path"].parent)
        by_name[pdf.name] = pdf
    failures = 0
    materials = db.scalars(
        select(Material).where(Material.source_path.is_not(None)).order_by(Material.id)
    ).all()

    if not materials:
        print("No PDF-ingested materials in the database yet.")
        return 0

    for material in materials:
        path = by_name.get(material.source_path or "")
        print(f"\n  {material.title}  (material {material.id}, {material.chunk_count} chunks)")
        if path is None:
            print(f"    ? source PDF {material.source_path!r} is not in this folder -- skipped")
            continue
        checks = ingest.verify_material(db, material.id, path, sample=args.sample)
        failures += report_checks(checks)
    return failures


def report_checks(checks: list[ingest.ChunkCheck]) -> int:
    """Print the sampled span checks. Returns how many failed."""
    failures = 0
    for c in checks:
        mark = "PASS" if c.ok else "FAIL"
        if not c.ok:
            failures += 1
        print(f"    [{mark}] chunk {c.chunk_id:<6} p.{c.page_no:<4} "
              f"[{c.span[0]}:{c.span[1]}]  slice={c.slice_matches}  "
              f"on_page={c.appears_on_page}")
        print(f"           \"{c.preview}...\"")
    return failures


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=PDF_DIR)
    ap.add_argument("--file", type=Path)
    ap.add_argument("--title")
    ap.add_argument("--kind", default="textbook", choices=ingest.INGESTABLE_KINDS)
    ap.add_argument("--course")
    ap.add_argument("--course-title", help="create the course if --course is unknown")
    ap.add_argument("--department", help="department for a newly created course")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--sample", type=int, default=3)
    args = ap.parse_args()

    if args.file:
        if not args.file.exists():
            sys.exit(f"No such file: {args.file}")
        plan = [{"path": args.file, "title": args.title or args.file.stem,
                 "kind": args.kind, "course": args.course}]
    else:
        if not args.dir.exists():
            sys.exit(f"No such folder: {args.dir}")
        plan = plan_from_dir(args.dir)

    if not plan:
        print(f"No PDFs in {args.dir}.")
        print("Drop the course material there and run this again. Until then the")
        print("stand-in corpus in backend/data/seed/corpus.json stands in for it,")
        print("and everything downstream of retrieval is already testable.")
        return

    if args.dry_run:
        do_dry_run(plan)
        return

    db = get_sessionmaker()()
    try:
        if args.verify:
            failures = do_verify(db, plan, args)
            print(f"\n{'FAILED' if failures else 'PASS'} -- {failures} chunk(s) did not verify.")
            sys.exit(1 if failures else 0)

        course = resolve_course(db, args.course, args.course_title, args.department)
        print(f"Ingesting {len(plan)} PDF(s) into {course.code} - {course.title}")
        do_ingest(db, plan, course, args)
        print("\nDone. Re-run backend/scripts/calibrate_threshold.py -- the refusal")
        print("threshold is corpus-specific and the corpus just changed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
