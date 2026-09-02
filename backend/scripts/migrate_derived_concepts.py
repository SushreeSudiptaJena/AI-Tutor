"""concept-001 -- give topics and concepts a provenance, so derived rows exist.

    .venv/Scripts/python.exe backend/scripts/migrate_derived_concepts.py [--dry-run]

**Why this file exists.** No Alembic, by decision (CLAUDE.md), and
`create_all()` only creates tables that are *missing* -- it will not add a
column to a table that already exists. `topics` and `concepts` are already in
the shared database with the whole CSW2 and PH101 syllabus in them, so the
change has to be spelled out.

Every statement is idempotent, and every new column is nullable or carries a
DEFAULT, so nothing existing breaks and no row is rewritten by hand.

`source` defaults to `'seed'` **and is backfilled to `'seed'`**, which is the
truth: every row that exists when this runs was written by `seed.py` from
`backend/data/seed/concepts.json`. Getting that backfill wrong in the other
direction would be quietly catastrophic -- see `prune_removed()` in seed.py,
which deletes concepts no seed file defines and now spares only the rows this
column marks as derived.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "backend")

from sqlalchemy import inspect, text  # noqa: E402

from app.db import get_engine  # noqa: E402

DRY = "--dry-run" in sys.argv

WANT = {
    "topics": ("source",),
    "concepts": ("source", "material_id", "page_start", "page_end", "summary"),
}

STATEMENTS = [
    ("topics.source",
     "ALTER TABLE topics ADD COLUMN IF NOT EXISTS source VARCHAR(10) "
     "NOT NULL DEFAULT 'seed'"),
    ("concepts.source",
     "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS source VARCHAR(10) "
     "NOT NULL DEFAULT 'seed'"),
    ("concepts.material_id",
     "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS material_id INTEGER"),
    ("concepts.page_start",
     "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS page_start INTEGER"),
    ("concepts.page_end",
     "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS page_end INTEGER"),
    ("concepts.summary",
     "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS summary TEXT"),
    # Deleting a book must not delete the syllabus read out of it: the concept
    # keeps its page range and simply stops naming a material. ON DELETE SET
    # NULL, never CASCADE.
    ("concepts.material_id -> materials",
     """
     DO $$
     BEGIN
       IF NOT EXISTS (
         SELECT 1 FROM pg_constraint WHERE conname = 'concepts_material_id_fkey'
       ) THEN
         ALTER TABLE concepts
           ADD CONSTRAINT concepts_material_id_fkey
           FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE SET NULL;
       END IF;
     END $$;
     """),
    # Every listing this feature adds is "the concepts of one course, by
    # source". Without these, that is a sequential scan per page.
    ("index concepts(source)",
     "CREATE INDEX IF NOT EXISTS ix_concepts_source ON concepts (source)"),
    ("index topics(source)",
     "CREATE INDEX IF NOT EXISTS ix_topics_source ON topics (source)"),
]


def describe(engine) -> None:
    insp = inspect(engine)
    for table, cols in WANT.items():
        present = {c["name"]: c for c in insp.get_columns(table)}
        for name in cols:
            c = present.get(name)
            if c is None:
                print(f"    {table}.{name:<14} MISSING")
            else:
                print(f"    {table}.{name:<14} {str(c['type']):<14} "
                      f"{'NULL ok' if c['nullable'] else 'NOT NULL'}")


def counts(engine) -> None:
    with engine.connect() as conn:
        for table in ("topics", "concepts"):
            try:
                rows = conn.execute(
                    text(f"SELECT source, count(*) FROM {table} GROUP BY source "
                         "ORDER BY source")
                ).all()
                print(f"    {table:<10} " + ", ".join(f"{s}={n}" for s, n in rows))
            except Exception:  # noqa: BLE001 -- the column may not exist yet
                print(f"    {table:<10} (no source column yet)")


def main() -> int:
    engine = get_engine()

    print("before:")
    describe(engine)
    counts(engine)

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
    counts(engine)

    insp = inspect(engine)
    missing = [
        f"{t}.{n}"
        for t, cols in WANT.items()
        for n in cols
        if n not in {c["name"] for c in insp.get_columns(t)}
    ]
    if missing:
        print(f"\nMIGRATION DID NOT TAKE -- missing={missing}")
        return 1
    print("\nmigration OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
