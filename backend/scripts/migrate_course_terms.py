"""admin-005 -- give a course a semester, admission batches and term dates.

    .venv/Scripts/python.exe backend/scripts/migrate_course_terms.py [--dry-run]

**Why this file exists.** No Alembic, by decision (CLAUDE.md), and
`create_all()` only creates tables that are *missing* -- it will not add a
column to a table that already exists. `courses` is already in the shared
database with rows in it, so the change has to be spelled out.

Every statement is idempotent: running it twice is safe, and running it against
a database `create_all()` built fresh is a no-op.

Nothing is dropped and no row is rewritten. Existing courses simply gain NULL
semester / term dates and a NULL admission_batches, which is exactly what the
contract says a course that predates these fields returns.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "backend")

from sqlalchemy import inspect, text  # noqa: E402

from app.db import get_engine  # noqa: E402

DRY = "--dry-run" in sys.argv

COLUMNS = ("semester", "admission_batches", "term_start", "term_end")

STATEMENTS = [
    ("add semester",
     "ALTER TABLE courses ADD COLUMN IF NOT EXISTS semester INTEGER"),
    ("add admission_batches",
     "ALTER TABLE courses ADD COLUMN IF NOT EXISTS admission_batches INTEGER[]"),
    ("add term_start",
     "ALTER TABLE courses ADD COLUMN IF NOT EXISTS term_start DATE"),
    ("add term_end",
     "ALTER TABLE courses ADD COLUMN IF NOT EXISTS term_end DATE"),
]


def describe(engine) -> None:
    cols = {c["name"]: c for c in inspect(engine).get_columns("courses")}
    for name in COLUMNS:
        c = cols.get(name)
        if c is None:
            print(f"    {name:<20} MISSING")
        else:
            print(f"    {name:<20} {str(c['type']):<12} "
                  f"{'NULL ok' if c['nullable'] else 'NOT NULL'}")


def main() -> int:
    engine = get_engine()

    print("before:")
    describe(engine)

    print("\nwould run:" if DRY else "\nrunning:")
    for label, sql in STATEMENTS:
        print(f"    {label}")
        if not DRY:
            with engine.begin() as conn:
                conn.execute(text(sql))

    if DRY:
        print("\nNothing was changed. Drop --dry-run to apply.")
        return 0

    print("\nafter:")
    describe(engine)

    cols = {c["name"]: c for c in inspect(engine).get_columns("courses")}
    missing = [c for c in COLUMNS if c not in cols]
    not_null = [c for c in COLUMNS if c in cols and not cols[c]["nullable"]]
    if missing or not_null:
        print(f"\nMIGRATION DID NOT TAKE -- missing={missing} not_null={not_null}")
        return 1
    print("\nmigration OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
