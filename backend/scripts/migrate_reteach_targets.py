"""teacher-008 -- let a reteach unit target a prerequisite concept.

    .venv/Scripts/python.exe backend/scripts/migrate_reteach_targets.py [--dry-run]

**Why this file exists.** The stack has no Alembic on purpose (see CLAUDE.md),
and `create_all()` only creates tables that are *missing* -- it will not add a
column to a table that already exists, nor relax a NOT NULL. `reteach_units` is
already in the shared database with rows in it, so the change has to be spelled
out.

Every statement is idempotent, so running it twice is safe and running it on a
fresh database created by `create_all()` is a no-op.

Nothing is dropped and no row is rewritten. Existing units keep their
misconception and simply gain a NULL `concept_id`.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "backend")

from sqlalchemy import inspect, text  # noqa: E402

from app.db import get_engine  # noqa: E402

DRY = "--dry-run" in sys.argv

STATEMENTS = [
    ("add concept_id",
     "ALTER TABLE reteach_units ADD COLUMN IF NOT EXISTS concept_id INTEGER"),
    ("point it at concepts",
     """DO $$ BEGIN
          ALTER TABLE reteach_units
            ADD CONSTRAINT fk_reteach_units_concept
            FOREIGN KEY (concept_id) REFERENCES concepts (id);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$"""),
    ("index it",
     "CREATE INDEX IF NOT EXISTS ix_reteach_units_concept_id "
     "ON reteach_units (concept_id)"),
    ("let misconception_id be null",
     "ALTER TABLE reteach_units ALTER COLUMN misconception_id DROP NOT NULL"),
]


def describe(engine) -> None:
    cols = {c["name"]: c for c in inspect(engine).get_columns("reteach_units")}
    for name in ("misconception_id", "concept_id"):
        c = cols.get(name)
        state = "MISSING" if c is None else ("NULL ok" if c["nullable"] else "NOT NULL")
        print(f"    {name:<18} {state}")


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

    cols = {c["name"]: c for c in inspect(engine).get_columns("reteach_units")}
    ok = ("concept_id" in cols
          and cols["concept_id"]["nullable"]
          and cols["misconception_id"]["nullable"])
    print("\nmigration OK" if ok else "\nMIGRATION DID NOT TAKE -- check the errors above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
