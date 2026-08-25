"""Report seeded content in the database that no seed file defines. READ ONLY.

    .venv/Scripts/python.exe backend/scripts/find_phantoms.py

`infra-006` gave `seed.py` a prune pass, but a prune only ever runs when
somebody re-seeds, and it is scoped to the ONE course the seed files describe
(`course.json -> primary_course`). That leaves three ways a phantom can still
be sitting in the shared database, and none of them is visible from the seed
files or from the code:

  1. PRE-DATING THE FIX -- a row removed from a seed file before 2026-08-24 in
     a course nobody has re-seeded since.
  2. OUT OF REACH -- content belonging to a course the seed files do not
     describe (`PH101`, `CS-C`, ...). Correctly out of scope for a CSW2 run --
     a run that seeds one course must never delete another's -- but it also
     means nothing will ever prune it.
  3. UNPARENTED -- `Misconception.topic_id` and `PracticeItem.concept_id` are
     nullable, and every prune pass joins through `Topic` to reach a
     `course_id`. A row with a null parent is in no course, so no run of any
     kind can see it.

This script only reports. It never deletes: what to do about a phantom is a
content decision, and the answer for anything with dependents is "leave it
alone" -- see `prune_removed()`.

Exit code is 1 only for case 1 in the primary course, which would be a real
regression in the prune. Cases 2 and 3 are facts about the design and exit 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from app.db import get_sessionmaker
from app.models import (
    Attempt,
    Concept,
    Course,
    DiagnosticItem,
    Gap,
    Mastery,
    Misconception,
    MisconceptionDiagnosis,
    PracticeItem,
    ReteachUnit,
    Topic,
    UncertaintyFlag,
)

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"


def load(name: str) -> dict:
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


def count(db: OrmSession, model, condition) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(condition)) or 0)


# The dependent checks are deliberately the SAME ones `prune_removed()` uses.
# If they drift, this script starts reporting a row as safe to delete that the
# prune would refuse to touch -- worse than not reporting at all.
def dependents(db: OrmSession, kind: str, row) -> dict[str, int]:
    if kind == "concept":
        d = {
            "gaps": count(db, Gap, Gap.concept_id == row.id),
            "mastery": count(db, Mastery, Mastery.concept_id == row.id),
            "practice": count(db, PracticeItem, PracticeItem.concept_id == row.id),
            "diagnostic": count(db, DiagnosticItem, DiagnosticItem.concept_id == row.id),
        }
    elif kind == "misconception":
        d = {
            "diagnoses": count(db, MisconceptionDiagnosis,
                               MisconceptionDiagnosis.misconception_id == row.id),
            "reteach units": count(db, ReteachUnit,
                                   ReteachUnit.misconception_id == row.id),
        }
    elif kind == "seeded practice item":
        d = {"attempts": count(db, Attempt, Attempt.practice_item_id == row.id)}
    elif kind == "topic":
        d = {
            "concepts": count(db, Concept, Concept.topic_id == row.id),
            "misconceptions": count(db, Misconception, Misconception.topic_id == row.id),
            "uncertainty flags": count(db, UncertaintyFlag,
                                       UncertaintyFlag.topic_id == row.id),
        }
    else:
        d = {}
    return {k: v for k, v in d.items() if v}


def rows_for_course(db: OrmSession, course: Course):
    """Every seeded-content row reachable from one course, by kind."""
    return [
        ("topic", db.scalars(
            select(Topic).where(Topic.course_id == course.id)
            .order_by(Topic.slug)).all()),
        ("concept", db.scalars(
            select(Concept).join(Topic, Topic.id == Concept.topic_id)
            .where(Topic.course_id == course.id).order_by(Concept.slug)).all()),
        ("misconception", db.scalars(
            select(Misconception).join(Topic, Topic.id == Misconception.topic_id)
            .where(Topic.course_id == course.id).order_by(Misconception.slug)).all()),
        ("seeded practice item", db.scalars(
            select(PracticeItem)
            .join(Concept, Concept.id == PracticeItem.concept_id)
            .join(Topic, Topic.id == Concept.topic_id)
            .where(Topic.course_id == course.id, PracticeItem.is_seed.is_(True))
            .order_by(PracticeItem.id)).all()),
    ]


def label_of(row) -> str:
    return getattr(row, "slug", None) or (row.prompt[:60] + "...")


def show(db: OrmSession, kind: str, row, verdict: str) -> None:
    deps = dependents(db, kind, row)
    detail = ", ".join(f"{v} {k}" for k, v in deps.items())
    fate = f"KEPT -- has {detail}" if deps else "orphan, a prune would delete it"
    print(f"    {verdict:<13}{kind:<22}{label_of(row)!r}")
    print(f"    {'':<13}{'':<22}-> {fate}")


def main() -> None:
    data = {
        "course": load("course.json"),
        "concepts": load("concepts.json"),
        "misconceptions": load("misconceptions.json"),
        "practice": load("practice.json"),
    }
    primary_code = data["course"]["primary_course"]
    # The natural keys `seed.py` upserts on, so "defined" means here exactly
    # what it means there.
    defined = {
        "topic": {t["slug"] for t in data["concepts"]["topics"]},
        "concept": {c["slug"] for c in data["concepts"]["concepts"]},
        "misconception": {m["slug"] for m in data["misconceptions"]["misconceptions"]},
        "seeded practice item": {i["prompt"] for i in data["practice"]["items"]},
    }

    Session = get_sessionmaker()
    regressions = 0
    with Session() as db:
        courses = db.scalars(select(Course).order_by(Course.code)).all()
        print(f"Seed files describe: {primary_code}")
        print(f"Courses in the database: {', '.join(c.code for c in courses)}")

        for course in courses:
            print(f"\n=== {course.code} -- {course.title}")
            is_primary = course.code == primary_code
            found = 0
            for kind, rows in rows_for_course(db, course):
                for row in rows:
                    key = row.prompt if kind == "seeded practice item" else row.slug
                    if is_primary:
                        if key in defined[kind]:
                            continue
                        regressions += 1
                        found += 1
                        show(db, kind, row, "PHANTOM")
                    else:
                        found += 1
                        show(db, kind, row, "OUT-OF-REACH")
            if not found:
                print("    clean -- every row is defined by a seed file" if is_primary
                      else "    no seeded content rows (corpus-only course)")

        # Case 3: unparented rows are in no course at all, so the loop above
        # cannot have printed them and neither can any prune.
        print("\n=== Unparented (in no course -- invisible to every prune)")
        unparented = [
            ("misconception", db.scalars(
                select(Misconception).where(Misconception.topic_id.is_(None))
                .order_by(Misconception.slug)).all()),
            ("seeded practice item", db.scalars(
                select(PracticeItem).where(
                    PracticeItem.concept_id.is_(None), PracticeItem.is_seed.is_(True)
                ).order_by(PracticeItem.id)).all()),
        ]
        if any(rows for _, rows in unparented):
            for kind, rows in unparented:
                for row in rows:
                    show(db, kind, row, "UNPARENTED")
        else:
            print("    none")

    print()
    if regressions:
        print(f"FAIL -- {regressions} phantom row(s) in {primary_code} that the prune "
              f"should have removed. Re-run seed.py and read its output.")
        sys.exit(1)
    print(f"PASS -- no phantom rows in {primary_code}.")


if __name__ == "__main__":
    main()
