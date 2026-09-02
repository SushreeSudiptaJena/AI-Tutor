"""Load backend/data/seed/*.json into the database.

    .venv/Scripts/python.exe backend/scripts/seed.py

Idempotent: safe to run repeatedly. Everything is matched on a natural key
(course code, concept slug, email, misconception slug), so re-running updates
rather than duplicating.

It validates before it writes, and refuses to seed on a broken cross-reference.
The check that matters most: every practice item must have at least one wrong
option that some misconception's wrong_answer_pattern matches. An item without
one silently produces the demo's weakest moment - a wrong answer with no
diagnosis - and you would only find out on stage.

Flags:
    --skip-corpus   don't (re)embed the stand-in corpus, much faster
    --quiet         less output
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select, func
from sqlalchemy.orm import Session as OrmSession

from app.db import get_sessionmaker
from app.security import hash_password
from app.config import MAJOR_YEARS
from app.models import (
    Attempt,
    AuditLog,
    Concept,
    Course,
    Department,
    DiagnosticItem,
    Gap,
    Mastery,
    Material,
    Chunk,
    Misconception,
    MisconceptionDiagnosis,
    PracticeItem,
    ReteachUnit,
    SourcedContent,
    Topic,
    UncertaintyFlag,
    User,
    course_prerequisites,
    CourseTeacher,
    Batch,
)

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"
QUIET = "--quiet" in sys.argv
SKIP_CORPUS = "--skip-corpus" in sys.argv


def log(*a):
    if not QUIET:
        print(*a)


def load(name: str) -> dict:
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


def seeded_hash(plain: str, email: str) -> str:
    """Same hashing as a real signup -- imported, not reimplemented, so seeded
    passwords can never drift out of sync with app.security.verify_password.

    The salt is derived from the email so re-seeding produces an identical hash
    and the row genuinely does not change.
    """
    salt = hashlib.sha256(email.encode()).hexdigest()[:32]
    return hash_password(plain, salt=salt)


# ---------------------------------------------------------------------------
# Validation - runs before anything is written
# ---------------------------------------------------------------------------

def validate(data: dict) -> list[str]:
    errors: list[str] = []

    concept_slugs = {c["slug"] for c in data["concepts"]["concepts"]}
    topic_slugs = {t["slug"] for t in data["concepts"]["topics"]}
    course_codes = {c["code"] for c in data["course"]["courses"]}

    for c in data["concepts"]["concepts"]:
        if c["topic"] not in topic_slugs:
            errors.append(f"concept '{c['slug']}' references unknown topic '{c['topic']}'")
        if c.get("prerequisite_course") and c["prerequisite_course"] not in course_codes:
            errors.append(f"concept '{c['slug']}' references unknown course '{c['prerequisite_course']}'")

    for i, item in enumerate(data["diagnostic"]["items"]):
        if item["concept"] not in concept_slugs:
            errors.append(f"diagnostic[{i}] references unknown concept '{item['concept']}'")
        if item["correct_answer"] not in item["options"]:
            errors.append(f"diagnostic[{i}] correct_answer is not among its options")

    misc_by_type: dict[str, list[dict]] = {}
    for m in data["misconceptions"]["misconceptions"]:
        misc_by_type.setdefault(m["problem_type"], []).append(m)
        if m["topic"] not in topic_slugs:
            errors.append(f"misconception '{m['slug']}' references unknown topic '{m['topic']}'")
        if m.get("wrong_answer_pattern"):
            try:
                re.compile(m["wrong_answer_pattern"])
            except re.error as exc:
                errors.append(f"misconception '{m['slug']}' has an invalid regex: {exc}")

    # The check that protects the demo's best moment.
    for i, item in enumerate(data["practice"]["items"]):
        if item["concept"] not in concept_slugs:
            errors.append(f"practice[{i}] references unknown concept '{item['concept']}'")
        if item["correct_answer"] not in item["options"]:
            errors.append(f"practice[{i}] correct_answer is not among its options")

        wrong = [o for o in item["options"] if o != item["correct_answer"]]
        candidates = misc_by_type.get(item["problem_type"], [])
        if not candidates:
            errors.append(
                f"practice[{i}] problem_type '{item['problem_type']}' has no misconceptions"
            )
            continue
        diagnosable = [
            o for o in wrong
            for m in candidates
            if m.get("wrong_answer_pattern") and re.search(m["wrong_answer_pattern"], o)
        ]
        if not diagnosable:
            errors.append(
                f"practice[{i}] ('{item['prompt'][:45]}...') has NO wrong option matching any "
                f"misconception pattern for problem_type '{item['problem_type']}' - "
                f"a wrong answer here would produce no diagnosis"
            )

    known = {m["slug"] for m in data["misconceptions"]["misconceptions"]}
    dc = data["demo_class"]
    for bucket in ("confirmed_misconceptions", "denied_misconceptions"):
        for slug in dc.get(bucket, {}):
            if slug not in known:
                errors.append(f"demo_class.{bucket} references unknown misconception '{slug}'")
    for slug in dc.get("gap_counts", {}):
        if slug not in concept_slugs:
            errors.append(f"demo_class.gap_counts references unknown concept '{slug}'")
    for r in dc.get("reteach_units", []):
        if r["misconception"] not in known:
            errors.append(f"reteach unit references unknown misconception '{r['misconception']}'")

    return errors


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

def seed_structure(db: OrmSession, data: dict) -> dict[str, Course]:
    for d in data["course"]["departments"]:
        if not db.scalar(select(Department).where(Department.name == d["name"])):
            db.add(Department(name=d["name"]))
    db.flush()
    depts = {d.name: d for d in db.scalars(select(Department)).all()}

    courses: dict[str, Course] = {}
    for c in data["course"]["courses"]:
        row = db.scalar(select(Course).where(Course.code == c["code"]))
        if row is None:
            row = Course(code=c["code"])
            db.add(row)
        row.title = c["title"]
        row.department_id = depts[c["department"]].id if c.get("department") else None
        courses[c["code"]] = row
    db.flush()

    db.execute(delete(course_prerequisites))
    for c in data["course"]["courses"]:
        for pre in c.get("prerequisites", []):
            db.execute(
                course_prerequisites.insert().values(
                    course_id=courses[c["code"]].id, prerequisite_id=courses[pre].id
                )
            )
    log(f"  courses          {len(courses)}")
    return courses


def seed_map(db: OrmSession, data: dict, courses: dict[str, Course], primary: Course):
    topics: dict[str, Topic] = {}
    for t in data["concepts"]["topics"]:
        row = db.scalar(
            select(Topic).where(Topic.course_id == primary.id, Topic.slug == t["slug"])
        )
        if row is None:
            row = Topic(course_id=primary.id, slug=t["slug"])
            db.add(row)
        row.name = t["name"]
        row.source = "seed"
        topics[t["slug"]] = row
    db.flush()

    concepts: dict[str, Concept] = {}
    for c in data["concepts"]["concepts"]:
        row = db.scalar(select(Concept).where(Concept.slug == c["slug"]))
        if row is None:
            row = Concept(slug=c["slug"])
            db.add(row)
        row.name = c["name"]
        row.source = "seed"
        row.topic_id = topics[c["topic"]].id
        pre = c.get("prerequisite_course")
        row.prerequisite_course_id = courses[pre].id if pre else None
        concepts[c["slug"]] = row
    db.flush()
    log(f"  topics           {len(topics)}")
    log(f"  concepts         {len(concepts)}")
    return topics, concepts


def seed_users(db: OrmSession, data: dict, courses: dict[str, Course]) -> dict[str, User]:
    users: dict[str, User] = {}
    for u in data["users"]["users"]:
        row = db.scalar(select(User).where(User.email == u["email"]))
        if row is None:
            row = User(email=u["email"])
            db.add(row)
        row.full_name = u["full_name"]
        row.role = u["role"]
        row.password_hash = seeded_hash(u["password"], u["email"])
        row.course_id = courses[u["course"]].id if u.get("course") else None
        row.preferred_language = u.get("preferred_language", "en")
        users[u["email"]] = row
    db.flush()

    # teacher-009: a seeded teacher needs the ASSIGNMENT row too, not just a
    # course_id. The console lists the subjects a teacher is assigned to
    # (course_teachers, admin-009), so a teacher with a course_id and no
    # assignment sees an empty switcher and cannot move between subjects --
    # which is exactly what the demo teacher did until this was added.
    for u in data["users"]["users"]:
        row = users[u["email"]]
        if row.role != "teacher" or row.course_id is None:
            continue
        # The demo teacher teaches more than one subject on purpose: the
        # console's subject switcher, My Classes and the material library all
        # look broken with a single assignment, and a real teacher has
        # several. Any course carrying an ingested corpus qualifies.
        with_corpus = {
            cid for (cid,) in db.execute(
                select(Material.course_id)
                .where(Material.ingest_status == "complete", Material.status == "active")
                .distinct()
            ).all()
        }
        # ...except the retired physics stand-in (PH101/PH000). It still has
        # a corpus and is deliberately left in the database, but it is not a
        # subject anybody teaches now, and listing it as one of this
        # teacher's classes would be a lie on the demo screen.
        retired = {
            cid for (cid,) in db.execute(
                select(Course.id).where(Course.code.like("PH%"))
            ).all()
        }
        with_corpus -= retired
        for course_id in {row.course_id, *with_corpus}:
            link = db.scalar(
                select(CourseTeacher).where(
                    CourseTeacher.course_id == course_id,
                    CourseTeacher.user_id == row.id,
                )
            )
            if link is None:
                db.add(CourseTeacher(course_id=course_id, user_id=row.id))
    db.flush()

    log(f"  users            {len(users)}")
    return users


def seed_batch(db: OrmSession, primary: Course, courses: dict[str, Course],
               users: dict[str, User]) -> Batch:
    """The demo cohort (admin-009/student-010), so the flow is walkable.

    Without one, a fresh signup reaches onboarding and finds no batch to join,
    and the teacher console shows a subject belonging to no cohort. The year
    is fixed rather than derived from today's date: a seed that produces a
    different cohort each year is a seed whose screenshots stop matching.
    """
    dept_id = primary.department_id
    start = 2026
    batch = db.scalar(
        select(Batch).where(
            Batch.major == "btech",
            Batch.department_id == dept_id,
            Batch.start_year == start,
        )
    )
    if batch is None:
        batch = Batch(major="btech", department_id=dept_id,
                      start_year=start, end_year=start + MAJOR_YEARS["btech"])
        db.add(batch)
        db.flush()

    # The subjects this cohort takes: the demo course, plus any other course
    # in the same department that has a real corpus behind it.
    #
    # "has a corpus" is the filter that matters, and it excludes the
    # PREREQUISITE course (CSW1) on purpose. A prerequisite is what the
    # cohort should have learned BEFORE -- it is already modelled by
    # course_prerequisites and is what gap attribution names. Listing it as
    # a subject they are currently taking would put an empty dashboard one
    # click away, and would make the default subject for a new student the
    # one with nothing in it.
    with_corpus = {
        cid for (cid,) in db.execute(
            select(Material.course_id)
            .where(Material.ingest_status == "complete", Material.status == "active")
            .distinct()
        ).all()
    }
    # Candidates come from the DATABASE, not from the seed file's course map:
    # courses ingested by an earlier run (CS-C) are real subjects of this
    # department and belong in the cohort, but they never appear in this
    # seed's data files.
    candidates = db.scalars(
        select(Course).where(Course.department_id == dept_id).order_by(Course.code)
    ).all()
    wanted = [primary] + [
        c for c in candidates
        if c.id != primary.id and c.id in with_corpus
    ]
    have = {c.id for c in batch.courses}
    for c in wanted:
        if c.id not in have:
            batch.courses.append(c)

    # Converge rather than accumulate: a subject already linked but carrying
    # no corpus is dropped, so re-running the seed after a rule change fixes
    # the cohort instead of leaving yesterday's links behind. Only empty
    # subjects are pruned -- an admin's deliberate link to a subject that has
    # material is left alone, because the seed does not own that decision.
    keep_ids = {c.id for c in wanted}
    dropped = [c for c in batch.courses
               if c.id not in keep_ids and c.id not in with_corpus]
    for c in dropped:
        batch.courses.remove(c)
    if dropped:
        log(f"  batch pruned     {[c.code for c in dropped]} (no corpus)")

    # Seeded students belong to the cohort; their course_id (the ACTIVE
    # subject) is left exactly as the user seed set it.
    for u in users.values():
        if u.role == "student":
            u.batch_id = batch.id
    db.flush()
    log(f"  demo batch       {batch.major} {batch.start_year}-{batch.end_year}, "
        f"{len(batch.courses)} subjects")
    return batch


def seed_items(db: OrmSession, data: dict, primary: Course, concepts, topics):
    db.execute(delete(DiagnosticItem).where(DiagnosticItem.course_id == primary.id))
    for it in data["diagnostic"]["items"]:
        db.add(DiagnosticItem(
            course_id=primary.id, concept_id=concepts[it["concept"]].id,
            prompt=it["prompt"], kind=it.get("kind", "mcq"),
            options={"choices": it["options"]}, correct_answer=it["correct_answer"],
        ))
    log(f"  diagnostic items {len(data['diagnostic']['items'])}")

    misc: dict[str, Misconception] = {}
    for m in data["misconceptions"]["misconceptions"]:
        row = db.scalar(select(Misconception).where(Misconception.slug == m["slug"]))
        if row is None:
            row = Misconception(slug=m["slug"])
            db.add(row)
        row.topic_id = topics[m["topic"]].id
        row.problem_type = m["problem_type"]
        row.label = m["label"]
        row.description = m.get("description", "")
        row.wrong_answer_pattern = m.get("wrong_answer_pattern")
        misc[m["slug"]] = row
    db.flush()
    log(f"  misconceptions   {len(misc)}")

    # Upsert on the prompt text rather than delete-and-recreate: seeded items are
    # referenced by attempts, so deleting them violates a foreign key on the
    # second run. Idempotency is a requirement, not a nicety - this script runs
    # many times during a build.
    practice = []
    for it in data["practice"]["items"]:
        row = db.scalar(
            select(PracticeItem).where(
                PracticeItem.is_seed.is_(True), PracticeItem.prompt == it["prompt"]
            )
        )
        if row is None:
            row = PracticeItem(prompt=it["prompt"], is_seed=True)
            db.add(row)
        row.practice_set_id = None
        row.concept_id = concepts[it["concept"]].id
        row.problem_type = it["problem_type"]
        row.kind = it.get("kind", "mcq")
        row.options = {"choices": it["options"]}
        row.correct_answer = it["correct_answer"]
        practice.append(row)
    db.flush()
    log(f"  practice items   {len(practice)}")
    return misc, practice



# ---------------------------------------------------------------------------
# Pruning -- infra-006
# ---------------------------------------------------------------------------

def _count(db: OrmSession, model, condition) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(condition)) or 0)


def prune_removed(db: OrmSession, primary: Course, topics, concepts, misc, practice):
    """Delete seeded content that has vanished from the seed files.

    `seed.py` upserts by natural key, which makes it idempotent but also makes
    it one-directional: adding a concept to `concepts.json` adds a row, and
    removing one leaves the row behind forever. That row is not inert. It is a
    phantom -- `model-fields`, dropped from the seed when it failed the corpus
    evidence check, survived in the shared database and showed up months later
    as a concept in `GET /student/mastery` that no seed file defined. Anything
    that enumerates a whole course surfaces these; nothing else does, which is
    why they can sit unnoticed.

    `diagnostic_items` are exempt because `seed_items()` already deletes and
    recreates them wholesale, which prunes as a side effect.

    DERIVED CONTENT IS EXEMPT, AND THIS IS NOT OPTIONAL
    ---------------------------------------------------
    `concept-001` writes concepts and topics extracted from the corpus by
    `derive_concepts.py`. Every one of them is, by definition, absent from
    `concepts.json` -- which is exactly the test this function uses to decide
    what to delete. Without the `source == "seed"` filter below, the first
    `reset_demo_state.py` after a derivation run would silently delete the
    entire derived syllabus, and it would look like the derivation had never
    happened rather than like a bug. A seed file is the authority on seeded
    content and on nothing else.

    NOTHING WITH DEPENDENTS IS EVER DELETED
    ---------------------------------------
    A concept with a student's gap on it, a misconception behind a confirmed
    diagnosis, a practice item somebody has attempted -- deleting any of those
    takes real history with it, and a seed file is not the right authority to
    make that call. Those are reported and left alone, so a content lead who
    removed something by mistake sees it said out loud rather than discovering
    it as missing data. Only genuine orphans go.
    """
    plans = [
        (
            "concept",
            db.scalars(
                select(Concept)
                .join(Topic, Topic.id == Concept.topic_id)
                .where(Topic.course_id == primary.id,
                       # concept-001: a seed file is not the authority on
                       # anything it did not write. See the docstring.
                       Concept.source == "seed",
                       Concept.id.not_in([c.id for c in concepts.values()] or [-1]))
            ).all(),
            lambda row: {
                "gaps": _count(db, Gap, Gap.concept_id == row.id),
                "mastery": _count(db, Mastery, Mastery.concept_id == row.id),
                "practice": _count(db, PracticeItem, PracticeItem.concept_id == row.id),
                "diagnostic": _count(db, DiagnosticItem,
                                     DiagnosticItem.concept_id == row.id),
            },
        ),
        (
            "misconception",
            db.scalars(
                select(Misconception)
                .join(Topic, Topic.id == Misconception.topic_id)
                .where(Topic.course_id == primary.id,
                       Misconception.id.not_in([m.id for m in misc.values()] or [-1]))
            ).all(),
            lambda row: {
                "diagnoses": _count(db, MisconceptionDiagnosis,
                                    MisconceptionDiagnosis.misconception_id == row.id),
                "reteach units": _count(db, ReteachUnit,
                                        ReteachUnit.misconception_id == row.id),
            },
        ),
        (
            # Scoped to this course, like everything else here. An unscoped
            # version deleted ten retired PH101 practice items on its first
            # run -- the right outcome by luck, the wrong rule: `practice.json`
            # describes ONE course, so a run that seeds CSW2 must never be the
            # thing that removes another course's content. Two teammates
            # seeding two courses would otherwise wipe each other's.
            "seeded practice item",
            db.scalars(
                select(PracticeItem)
                .join(Concept, Concept.id == PracticeItem.concept_id)
                .join(Topic, Topic.id == Concept.topic_id)
                .where(
                    Topic.course_id == primary.id,
                    PracticeItem.is_seed.is_(True),
                    PracticeItem.id.not_in([p.id for p in practice] or [-1]),
                )
            ).all(),
            lambda row: {
                "attempts": _count(db, Attempt, Attempt.practice_item_id == row.id),
            },
        ),
        (
            # Topics last: a topic is only an orphan once its concepts and
            # misconceptions are gone, and the passes above may have just
            # removed the last of them.
            "topic",
            db.scalars(
                select(Topic).where(
                    Topic.course_id == primary.id,
                    # concept-001: same rule as concepts -- a derived topic is
                    # one chapter of an ingested book, and no seed file has
                    # anything to say about it.
                    Topic.source == "seed",
                    Topic.id.not_in([t.id for t in topics.values()] or [-1]),
                )
            ).all(),
            lambda row: {
                "concepts": _count(db, Concept, Concept.topic_id == row.id),
                "misconceptions": _count(db, Misconception,
                                         Misconception.topic_id == row.id),
                "uncertainty flags": _count(db, UncertaintyFlag,
                                            UncertaintyFlag.topic_id == row.id),
            },
        ),
    ]

    removed, kept = 0, []
    for label, rows, dependents_of in plans:
        for row in rows:
            name = getattr(row, "slug", None) or getattr(row, "prompt", "")[:45]
            deps = {k: v for k, v in dependents_of(row).items() if v}
            if deps:
                kept.append((label, name, deps))
                continue
            db.delete(row)
            removed += 1
            log(f"  pruned           {label} {name!r} (gone from the seed files)")
        db.flush()

    for label, name, deps in kept:
        detail = ", ".join(f"{v} {k}" for k, v in deps.items())
        log(f"  KEPT             {label} {name!r} is not in the seed files any more, "
            f"but has {detail} -- not deleted")

    if not removed and not kept:
        log("  prune            nothing stale")

def seed_corpus(db: OrmSession, data: dict, primary: Course, admin: User) -> int:
    corpus = data["corpus"]
    if not corpus.get("enabled", True):
        log("  corpus           disabled in corpus.json - skipped")
        return 0

    from app.services.embed import embed_documents

    total = 0
    for m in corpus["materials"]:
        row = db.scalar(
            select(Material).where(
                Material.course_id == primary.id, Material.title == m["title"]
            )
        )
        if row is None:
            row = Material(course_id=primary.id, title=m["title"])
            db.add(row)
        row.kind = m["kind"]
        row.page_count = m.get("page_count", 0)
        row.uploaded_by_id = admin.id
        row.status = "active"
        row.ingest_status = "complete"
        db.flush()

        db.execute(delete(Chunk).where(Chunk.material_id == row.id))
        texts = [p["text"] for p in m["passages"]]
        vectors = embed_documents(texts)
        for p, vec in zip(m["passages"], vectors):
            db.add(Chunk(
                material_id=row.id, page_no=p["page"], chapter=p.get("chapter"),
                char_start=0, char_end=len(p["text"]), text=p["text"], embedding=vec,
            ))
        row.chunk_count = len(m["passages"])
        total += len(m["passages"])
        log(f"    {m['title'][:38]:40} {len(m['passages']):3} chunks  ({m['kind']})")
    return total


def seed_demo_class(db: OrmSession, data: dict, primary: Course,
                    concepts, misc, practice, topics, teacher: User):
    """Pre-load class history so the teacher dashboard is not empty on demo day."""
    dc = data["demo_class"]
    n = dc.get("synthetic_students", 0)

    students: list[User] = []
    for i in range(1, n + 1):
        email = f"student{i:02d}@seed.local"
        row = db.scalar(select(User).where(User.email == email))
        if row is None:
            row = User(email=email)
            db.add(row)
        row.full_name = f"Student {i:02d}"
        row.role = "student"
        row.password_hash = seeded_hash("seeded-account-no-login", email)
        row.course_id = primary.id
        row.preferred_language = "en"
        students.append(row)
    db.flush()
    log(f"  synthetic class  {len(students)} students")

    ids = [s.id for s in students]
    db.execute(delete(MisconceptionDiagnosis).where(
        MisconceptionDiagnosis.attempt_id.in_(
            select(Attempt.id).where(Attempt.user_id.in_(ids))
        )
    ))
    db.execute(delete(Attempt).where(Attempt.user_id.in_(ids)))
    db.execute(delete(Gap).where(Gap.user_id.in_(ids)))

    for slug, count in dc.get("gap_counts", {}).items():
        for s in students[:count]:
            db.add(Gap(user_id=s.id, concept_id=concepts[slug].id,
                       detected_from="diagnostic", status="open"))
    db.flush()

    by_type: dict[str, PracticeItem] = {}
    for p in practice:
        by_type.setdefault(p.problem_type, p)

    def add_diagnoses(bucket: str, confirmed: bool | None):
        made = 0
        for slug, count in dc.get(bucket, {}).items():
            m = misc[slug]
            item = by_type.get(m.problem_type)
            if item is None:
                continue
            wrong = next(
                (o for o in item.options["choices"]
                 if o != item.correct_answer and m.wrong_answer_pattern
                 and re.search(m.wrong_answer_pattern, o)),
                "(seeded)",
            )
            for s in students[:count]:
                att = Attempt(user_id=s.id, practice_item_id=item.id,
                              answer=wrong, correct=False)
                db.add(att)
                db.flush()
                db.add(MisconceptionDiagnosis(
                    attempt_id=att.id, misconception_id=m.id,
                    source="pattern", confirmed=confirmed,
                ))
                made += 1
        return made

    c = add_diagnoses("confirmed_misconceptions", True)
    d = add_diagnoses("denied_misconceptions", False)
    log(f"  diagnoses        {c} confirmed, {d} denied (only confirmed reach the heatmap)")

    db.execute(delete(UncertaintyFlag))
    for f in dc.get("uncertainty_flags", []):
        t = f.get("topic")
        db.add(UncertaintyFlag(
            question=f["question"], alignment_score=f["alignment_score"],
            reason=f["reason"], course_id=primary.id,
            topic_id=topics[t].id if t else None, status="open",
        ))
    log(f"  uncertainty      {len(dc.get('uncertainty_flags', []))} flags")

    db.execute(delete(SourcedContent))
    for s in dc.get("sourced_content", []):
        db.add(SourcedContent(**{k: v for k, v in s.items() if k != "topic"}))
    log(f"  sourced content  {len(dc.get('sourced_content', []))} pending")

    db.execute(delete(ReteachUnit))
    for r in dc.get("reteach_units", []):
        db.add(ReteachUnit(
            misconception_id=misc[r["misconception"]].id, title=r["title"],
            body=r["body"], status=r.get("status", "draft"),
        ))
    log(f"  reteach units    {len(dc.get('reteach_units', []))} (draft - invisible to students)")


def main() -> None:
    data = {
        name: load(f"{name}.json")
        for name in ("course", "users", "concepts", "diagnostic",
                     "practice", "misconceptions", "demo_class", "corpus")
    }

    log("validating seed data...")
    errors = validate(data)
    if errors:
        print("\nSEED DATA IS INVALID - nothing was written:\n")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    log("  ok\n")

    db = get_sessionmaker()()
    try:
        log("seeding...")
        courses = seed_structure(db, data)
        primary = courses[data["course"]["primary_course"]]
        topics, concepts = seed_map(db, data, courses, primary)
        users = seed_users(db, data, courses)
        seed_batch(db, primary, courses, users)
        misc, practice = seed_items(db, data, primary, concepts, topics)

        admin = next(u for u in users.values() if u.role == "admin")
        teacher = next(u for u in users.values() if u.role == "teacher")

        if SKIP_CORPUS:
            log("  corpus           skipped (--skip-corpus)")
        else:
            log("  corpus (embedding, first run downloads the model)...")
            total = seed_corpus(db, data, primary, admin)
            log(f"  chunks           {total}")

        prune_removed(db, primary, topics, concepts, misc, practice)

        seed_demo_class(db, data, primary, concepts, misc, practice, topics, teacher)

        db.add(AuditLog(actor_id=admin.id, action="seed.run",
                        target=f"course:{primary.code}", detail={"source": "seed.py"}))
        db.commit()
        log("\nseeded ok")
        log(f"  log in as: {[u.email for u in users.values() if u.role != 'admin'][0]} / demo1234")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
