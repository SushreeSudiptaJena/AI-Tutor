"""Clear what a rehearsal leaves behind, and nothing else.

    .venv/Scripts/python.exe backend/scripts/reset_demo_state.py

Run this before a rehearsal or before the real demo. It deletes the
*transactional* state a run produces -- attempts, diagnoses, gaps, mastery,
generated practice, uncertainty flags -- and then re-seeds the demo class
history so the teacher dashboard is populated but not repetitive.

WHY THIS EXISTS RATHER THAN reset_db.py
---------------------------------------
`reset_db.py` drops every table, which includes `chunks`. That is over three
thousand rows carrying a 384-float embedding each, and regenerating them means
re-ingesting two books: roughly forty minutes of CPU. Nothing about tidying a
dashboard should cost that.

So this script never touches materials, chunks, courses, topics, concepts,
misconceptions, seeded practice items or users. Only the rows a demo run
creates.

    --dry-run     count what would be deleted, delete nothing
    --keep-flags  leave uncertainty_flags alone
    --no-reseed   do not re-run the demo class history afterwards
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from sqlalchemy import delete, func, select

from app.db import get_sessionmaker
from app.models import (
    Attempt,
    Gap,
    Mastery,
    MisconceptionDiagnosis,
    PracticeItem,
    PracticeSet,
    UncertaintyFlag,
)

# Order matters: children before parents, or the foreign keys refuse.
# MisconceptionDiagnosis -> Attempt -> PracticeItem -> PracticeSet.
PLAN = [
    ("misconception diagnoses", MisconceptionDiagnosis, None),
    ("practice attempts", Attempt, None),
    ("generated practice items", PracticeItem, PracticeItem.is_seed.is_(False)),
    ("practice sets", PracticeSet, None),
    ("gaps", Gap, None),
    ("mastery rows", Mastery, None),
]


def count(db, model, condition=None) -> int:
    stmt = select(func.count()).select_from(model)
    if condition is not None:
        stmt = stmt.where(condition)
    return int(db.scalar(stmt) or 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-flags", action="store_true")
    ap.add_argument("--no-reseed", action="store_true")
    args = ap.parse_args()

    plan = list(PLAN)
    if not args.keep_flags:
        plan.append(("uncertainty flags", UncertaintyFlag, None))

    db = get_sessionmaker()()
    try:
        print("\nWould delete:" if args.dry_run else "\nDeleting:")
        for label, model, condition in plan:
            n = count(db, model, condition)
            print(f"  {n:>6}  {label}")
            if not args.dry_run and n:
                stmt = delete(model)
                if condition is not None:
                    stmt = stmt.where(condition)
                db.execute(stmt)

        if args.dry_run:
            print("\nNothing was deleted. Drop --dry-run to do it.")
            return

        db.commit()
        print("\nUntouched: materials, chunks, courses, topics, concepts,")
        print("           misconceptions, seeded practice items, users.")
    finally:
        db.close()

    if args.no_reseed:
        print("\nNot re-seeding. The teacher dashboard will be EMPTY, which looks")
        print("broken even though it is correct -- run seed.py before demoing.")
        return

    print("\nRe-seeding the demo class history so the dashboard is populated...")
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("seed.py")), "--skip-corpus"],
        cwd=repo_root,
    )
    if result.returncode != 0:
        sys.exit("seed.py failed -- the dashboard may be empty.")


if __name__ == "__main__":
    main()
