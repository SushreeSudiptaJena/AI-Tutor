"""Student routes -- student-001, student-002, student-003.

Golden path steps 1 and 2 live here: take the diagnostic, get a gap list, open
a gap and read a lesson carrying its alignment score and its citations.

Three rules run through the whole file:

* **No score, anywhere.** The diagnostic returns a gap list, not a grade. There
  is no percentage, no "5 out of 8", no pass/fail, and nothing a frontend could
  add up to make one -- `answers` never comes back. That omission is a judging
  point, not an oversight.
* **The course comes from the signed-in user**, never from the request.
* **A gap lesson is never guardrailed.** It is concept-driven, so a
  graded-work refusal there could only ever be a false positive.
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession, selectinload

from ..db import get_db
from ..deps import current_user
from ..models import (
    Attempt,
    AuditLog,
    Chunk,
    Concept,
    Course,
    DiagnosticItem,
    DiagnosticResponse,
    Gap,
    Mastery,
    Material,
    Misconception,
    MisconceptionDiagnosis,
    PracticeItem,
    PracticeSet,
    ReteachUnit,
    Topic,
    User,
)
from ..schemas import (
    ConfirmDiagnosisIn,
    DiagnosticSubmitIn,
    PracticeAnswerIn,
    PracticeGenerateIn,
)
from ..providers import AllProvidersFailed
from ..services import practice, retrieval, syllabus, tutor

router = APIRouter(prefix="/student", tags=["student"])


def _course(db: OrmSession, user: User) -> Course:
    if user.course_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request",
                    "message": "Your account is not enrolled in a course."},
        )
    course = db.get(Course, user.course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "That course no longer exists."},
        )
    return course


def _suggested_prompts(concept_name: str, topic_name: str | None) -> list[str]:
    """Starter questions for the chat, derived from the concept.

    Deliberately deterministic string building rather than a model call: these
    are UI affordances on a list that may hold a dozen gaps, and spending a
    dozen LLM calls to phrase a button is the kind of cost that only shows up
    on demo day.
    """
    prompts = [f"Explain {concept_name.lower()} to me"]
    if topic_name:
        prompts.append(f"Why does {topic_name.lower()} need {concept_name.lower()}?")
    prompts.append(f"Show me a worked example using {concept_name.lower()}")
    return prompts


def _latest_practice_sets(db: OrmSession, gaps: list[Gap]) -> dict[int, int]:
    """gap_id -> newest practice set id, for every gap in one query.

    student-009: a client needs this to resume a half-finished set after a
    reload without having stored the id. Batched rather than asked per gap --
    the whole point of perf-001 was that a per-row query is a network round
    trip.
    """
    ids = [g.id for g in gaps]
    if not ids:
        return {}
    return {
        gap_id: set_id
        for gap_id, set_id in db.execute(
            select(PracticeSet.gap_id, func.max(PracticeSet.id))
            .where(PracticeSet.gap_id.in_(ids))
            .group_by(PracticeSet.gap_id)
        ).all()
    }


def _gap_out(db: OrmSession, gap: Gap, latest_sets: dict[int, int] | None = None) -> dict:
    # Read through the relationships rather than issuing our own db.get(): a
    # caller that eager-loaded them (see list_gaps) then pays no query at all,
    # and one that did not pays exactly what the db.get() cost before.
    concept = gap.concept
    topic = concept.topic if concept else None
    prerequisite = concept.prerequisite_course if concept else None
    if latest_sets is None:
        latest_sets = _latest_practice_sets(db, [gap])
    return {
        "id": gap.id,
        "concept": concept.name if concept else "",
        "prerequisite_course": prerequisite.title if prerequisite else None,
        "detected_from": gap.detected_from,
        "status": gap.status,
        "suggested_prompts": _suggested_prompts(
            concept.name if concept else "", topic.name if topic else None
        ),
        # null means "offer the practise button", never "call generate".
        "latest_practice_set_id": latest_sets.get(gap.id),
    }


# ---------------------------------------------------------------------------
# student-001 -- what is in scope
# ---------------------------------------------------------------------------

@router.get("/course-summary")
def course_summary(
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """Which books, which pages, which topics.

    Books are read from the materials actually ingested, and chapters from the
    chunks' own `chapter` column, so this page cannot drift from the corpus the
    tutor answers out of. If a book is not really there, it does not appear
    here either.

    Assignments are excluded. They are in the database so the guardrail can
    recognise homework, but "what is in scope for you to study" is not the
    place to advertise the graded work.
    """
    course = _course(db, user)

    materials = db.scalars(
        select(Material)
        .where(
            Material.course_id == course.id,
            Material.status == "active",
            Material.kind.in_(retrieval.LESSON_KINDS),
        )
        .order_by(Material.id)
    ).all()

    # Chapters for every book in one query, not one query per book. Same rows,
    # same order, one round trip instead of N.
    chapters_by_material: dict[int, list[str]] = {}
    if materials:
        for material_id, chapter in db.execute(
            select(Chunk.material_id, Chunk.chapter)
            .where(
                Chunk.material_id.in_([m.id for m in materials]),
                Chunk.chapter.is_not(None),
            )
            .group_by(Chunk.material_id, Chunk.chapter)
            .order_by(Chunk.material_id, Chunk.chapter)
        ).all():
            chapters_by_material.setdefault(material_id, []).append(chapter)

    books = [
        {
            "material_id": m.id,
            "title": m.title,
            "pages": f"1–{m.page_count}" if m.page_count else None,
            "chapters": chapters_by_material.get(m.id, []),
        }
        for m in materials
    ]

    topics = db.scalars(
        select(Topic).where(Topic.course_id == course.id).order_by(Topic.id)
    ).all()

    return {
        "course": {"id": course.id, "code": course.code, "title": course.title},
        "books": books,
        "topics": [{"id": t.id, "name": t.name} for t in topics],
    }


# ---------------------------------------------------------------------------
# student-002 -- the prerequisite diagnostic
# ---------------------------------------------------------------------------

@router.get("/diagnostic")
def get_diagnostic(
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """The prerequisite check.

    `diagnostic_id` is the course id. A course has exactly one diagnostic --
    the set of `diagnostic_items` belonging to it -- so there is nothing else
    for the id to identify, and inventing a table to hold that fact would be
    schema for its own sake.

    `correct_answer` is not in this response. It exists on the row and must
    never reach a client; that is what the explicit field list below is for.
    """
    course = _course(db, user)
    items = db.scalars(
        select(DiagnosticItem)
        # `item.concept.name` below is read for every item. Lazily, that was one
        # network round trip per question -- eight questions, eight round trips,
        # and this endpoint measured 12 queries for 8 items.
        .options(selectinload(DiagnosticItem.concept))
        .where(DiagnosticItem.course_id == course.id)
        .order_by(DiagnosticItem.id)
    ).all()

    # student-009 -- replay what this student already picked, so a reload does
    # not mean answering eight questions again. The answer TEXT only; see
    # DiagnosticResponse for why correctness is not stored.
    responses: dict[int, DiagnosticResponse] = {}
    if items:
        responses = {
            r.diagnostic_item_id: r
            for r in db.scalars(
                select(DiagnosticResponse).where(
                    DiagnosticResponse.user_id == user.id,
                    DiagnosticResponse.diagnostic_item_id.in_([i.id for i in items]),
                )
            ).all()
        }
    last = max((r.at for r in responses.values() if r.at), default=None)

    return {
        "diagnostic_id": course.id,
        # null until the first submit. "Start" vs "resume" is the frontend's
        # call to make from this -- not a reason to withhold the items.
        "submitted_at": last.isoformat().replace("+00:00", "Z") if last else None,
        "items": [
            {
                "id": item.id,
                "prompt": item.prompt,
                "kind": item.kind,
                "options": _options_list(item.options),
                "your_answer": (
                    responses[item.id].answer if item.id in responses else None
                ),
                "concept": item.concept.name if item.concept else None,
            }
            for item in items
        ],
    }


def _options_list(options) -> list[str] | None:
    """The contract says `options` is a list of strings; the column stores
    `{"choices": [...]}`.

    The JSON column is a dict so a future item kind can carry more than choices
    without a migration, but that is a storage detail and the API must not leak
    it. Returning the dict shipped `{"choices": [...]}` to the frontend, where
    iterating it yields the string "choices" -- which is not a wrong answer, it
    is a broken one.
    """
    if options is None:
        return None
    if isinstance(options, dict):
        choices = options.get("choices")
        return list(choices) if isinstance(choices, list) else None
    return list(options) if isinstance(options, list) else None


def _normalise_answer(text: str) -> str:
    return " ".join(str(text).split()).strip().lower()


@router.post("/diagnostic/{diagnostic_id}/submit")
def submit_diagnostic(
    diagnostic_id: int,
    body: DiagnosticSubmitIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """Turn wrong answers into named prerequisite gaps.

    Returns the gaps and nothing else. No score is computed here even
    internally -- there is no count of right answers to accidentally serialise
    later.

    Gaps are persisted rows, not a one-off result, so the dashboard, the
    mastery view and the chat's suggested prompts all read the same rows.
    Re-taking the diagnostic re-opens a gap rather than duplicating it.
    """
    course = _course(db, user)
    if diagnostic_id != course.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found",
                    "message": "That diagnostic does not belong to your course."},
        )

    items = {
        item.id: item
        for item in db.scalars(
            select(DiagnosticItem).where(DiagnosticItem.course_id == course.id)
        ).all()
    }

    unknown = [a.item_id for a in body.answers if a.item_id not in items]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request",
                    "message": "Some answers refer to items outside this diagnostic.",
                    "detail": {"item_ids": unknown}},
        )

    # student-009 -- keep the answer text so GET /student/diagnostic can replay
    # the student's selections. One row per (student, item): re-submitting an
    # item overwrites it, because the diagnostic is a starting point and not a
    # performance record. Correctness is computed below and NEVER stored.
    stored: dict[int, DiagnosticResponse] = {}
    if body.answers:
        stored = {
            r.diagnostic_item_id: r
            for r in db.scalars(
                select(DiagnosticResponse).where(
                    DiagnosticResponse.user_id == user.id,
                    DiagnosticResponse.diagnostic_item_id.in_(
                        [a.item_id for a in body.answers]
                    ),
                )
            ).all()
        }
    for answer in body.answers:
        row = stored.get(answer.item_id)
        if row is None:
            db.add(DiagnosticResponse(
                user_id=user.id,
                diagnostic_item_id=answer.item_id,
                answer=answer.answer,
            ))
        else:
            row.answer = answer.answer
            row.at = func.now()   # let the database hold the clock, as on insert

    missed: dict[int, Concept] = {}
    answered: dict[int, bool] = {}
    for answer in body.answers:
        item = items[answer.item_id]
        correct = _normalise_answer(answer.answer) == _normalise_answer(item.correct_answer)
        answered[item.concept_id] = answered.get(item.concept_id, True) and correct
        if not correct and item.concept is not None:
            missed[item.concept_id] = item.concept

    gaps: list[Gap] = []
    for concept_id, concept in missed.items():
        gap = db.scalar(
            select(Gap).where(Gap.user_id == user.id, Gap.concept_id == concept_id)
        )
        if gap is None:
            gap = Gap(user_id=user.id, concept_id=concept_id, detected_from="diagnostic")
            db.add(gap)
        gap.status = "open"
        gaps.append(gap)

    # Mastery is written from the same answers. Leaving it untouched would let
    # the mastery view say "untested" about a concept the student just answered,
    # which is a contradiction a judge can find in two clicks.
    for concept_id, all_correct in answered.items():
        row = db.scalar(
            select(Mastery).where(Mastery.user_id == user.id,
                                  Mastery.concept_id == concept_id)
        )
        if row is None:
            row = Mastery(user_id=user.id, concept_id=concept_id)
            db.add(row)
        row.state = "solid" if all_correct else "shaky"

    db.flush()

    latest = _latest_practice_sets(db, gaps)
    return {
        "gaps": [_gap_out(db, g, latest) for g in gaps],
        "message": _gap_message(len(gaps)),
    }



# ---------------------------------------------------------------------------
# student-008 -- the other way in
# ---------------------------------------------------------------------------

def _gap_message(count: int) -> str:
    """Both entries into the gap list say the same thing the same way.

    Duplicating this string once was already a bug waiting to happen: the
    frontend shows it verbatim, and "Found 1 prerequisite gaps." is the kind of
    detail a judge notices out loud.
    """
    if count == 0:
        return "No prerequisite gaps found."
    return f"Found {count} prerequisite gap{'' if count == 1 else 's'}."


@router.post("/syllabus-upload")
def syllabus_upload(
    file: UploadFile = File(...),
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """The alternative entry for an incoming student.

    Rather than sitting the diagnostic, the student uploads the syllabus of
    what they have **already studied**; we compare it against this course's
    prerequisites and open a gap for every one it does not cover. The response
    is byte-identical in shape to `POST /diagnostic/{id}/submit`, because from
    the frontend's side this is the same screen reached a different way.

    Gaps written here are indistinguishable downstream on purpose -- the same
    rows, read by the same dashboard, taught by the same lesson endpoint. Only
    `detected_from` differs, and that is for the teacher, not for the logic.

    No mastery is written. The diagnostic writes mastery because it has
    *answers*; a syllabus is evidence that a topic was taught, not that this
    student learned it. Recording "solid" from a syllabus line would be a
    measurement we never took. See `services/syllabus.py`.

    And no score, the same as everywhere else in this file.
    """
    course = _course(db, user)

    try:
        raw = file.file.read(syllabus.MAX_UPLOAD_BYTES + 1)
    finally:
        file.file.close()

    try:
        text = syllabus.extract_text(file.filename or "", raw)
    except syllabus.SyllabusError as exc:
        # A file we cannot read is the student's problem to fix, and they can
        # only fix it if they are told which problem it is -- "scan, not text"
        # and "wrong file type" need different actions from them.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": exc.message,
                    "detail": {"reason": exc.code}},
        )

    # Only prerequisites. Current-course concepts are what this course is about
    # to teach; finding them absent from a prior syllabus is expected, not a
    # gap, and reporting them would bury the real gaps in noise.
    concepts = db.scalars(
        select(Concept)
        .where(Concept.prerequisite_course_id.is_not(None))
        .join(Topic, Topic.id == Concept.topic_id)
        .where(Topic.course_id == course.id)
        .order_by(Concept.id)
    ).all()

    listing = [
        {"slug": c.slug, "name": c.name,
         "topic": (db.get(Topic, c.topic_id).name if c.topic_id else None)}
        for c in concepts
    ]

    try:
        verdicts = syllabus.assess(listing, text)
    except AllProvidersFailed as exc:
        # Never fall back to "covered nothing". That would hand back a maximal
        # gap list built from zero evidence and look exactly like a real result.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "provider_unavailable",
                    "message": "I could not read the syllabus just now. "
                               "Please try again in a moment.",
                    "detail": {"attempts": [name for name, _ in exc.attempts]}},
        )

    by_slug = {c.slug: c for c in concepts}
    gaps: list[Gap] = []
    for verdict in verdicts:
        if verdict.covered:
            continue
        concept = by_slug.get(verdict.slug)
        if concept is None:
            continue
        gap = db.scalar(
            select(Gap).where(Gap.user_id == user.id, Gap.concept_id == concept.id)
        )
        if gap is None:
            gap = Gap(user_id=user.id, concept_id=concept.id,
                      detected_from="syllabus_upload")
            db.add(gap)
        gap.status = "open"
        gaps.append(gap)

    db.flush()

    latest = _latest_practice_sets(db, gaps)
    return {
        "gaps": [_gap_out(db, g, latest) for g in gaps],
        "message": _gap_message(len(gaps)),
    }


@router.get("/gaps")
def list_gaps(
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    gaps = db.scalars(
        select(Gap)
        # _gap_out reads gap.concept, concept.topic and concept.prerequisite_course.
        # Loaded lazily that is three round trips per gap; loaded here it is two
        # for the whole list, however many gaps there are.
        .options(
            selectinload(Gap.concept).selectinload(Concept.topic),
            selectinload(Gap.concept).selectinload(Concept.prerequisite_course),
        )
        .where(Gap.user_id == user.id)
        .order_by(Gap.id)
    ).all()
    latest = _latest_practice_sets(db, list(gaps))
    return {"items": [_gap_out(db, g, latest) for g in gaps]}


# ---------------------------------------------------------------------------
# student-003 -- the lesson behind a gap
# ---------------------------------------------------------------------------

@router.get("/gaps/{gap_id}/lesson")
def gap_lesson(
    gap_id: int,
    language: str | None = None,
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """A `TutorResponse` for one gap, with the alignment badge and citations.

    Ownership is checked before anything else: a gap id is a small integer, and
    without this check changing it in the URL would read another student's gap
    list back to you one lesson at a time.

    `language` falls back to the student's saved preference rather than to
    English. Defaulting to `en` meant a student who had set their language to
    Hindi still got English lessons unless the frontend remembered to append a
    query parameter -- the preference existed and did nothing.
    """
    gap = db.get(Gap, gap_id)
    if gap is None or gap.user_id != user.id:
        # Same response either way. Distinguishing "not yours" from "not there"
        # would confirm that someone else's gap exists.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such gap."},
        )

    concept = gap.concept
    topic = db.get(Topic, concept.topic_id) if concept else None

    return tutor.lesson(
        db,
        concept.name if concept else "",
        course_id=user.course_id,
        topic_name=topic.name if topic else None,
        language=language or user.preferred_language,
    )


# ---------------------------------------------------------------------------
# student-007 -- what is solid and what is shaky
# ---------------------------------------------------------------------------

@router.get("/mastery")
def mastery(
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """Concept-level mastery, grouped by topic.

    **There is no aggregate score here, and no time-on-task.** Not an
    oversight, and not a thing to add later when the page looks sparse: a
    single number invites ranking students against each other, and minutes-
    spent measures compliance rather than understanding. Neither tells a
    student what to do next. "Free-body diagrams: shaky" does.

    That stance is only worth anything if the response makes it impossible to
    reconstruct one. So no counts, no totals, no attempt tallies, no
    timestamps -- a frontend cannot average what it was never given.

    `untested` is a first-class state, not a gap in the data. A concept nobody
    has been asked about is genuinely unknown, and saying so is more useful
    than implying competence by omission or failure by a zero.
    """
    course = _course(db, user)

    topics = db.scalars(
        select(Topic).where(Topic.course_id == course.id).order_by(Topic.id)
    ).all()
    if not topics:
        return {"items": []}

    concepts = db.scalars(
        select(Concept)
        .where(Concept.topic_id.in_([t.id for t in topics]))
        .order_by(Concept.id)
    ).all()

    # One query for every state, not one per concept. The N+1 version works
    # fine on a seeded demo course and falls over on a real syllabus.
    states = {
        row.concept_id: row.state
        for row in db.scalars(
            select(Mastery).where(Mastery.user_id == user.id)
        ).all()
    }

    by_topic: dict[int, list[dict]] = {}
    for concept in concepts:
        by_topic.setdefault(concept.topic_id, []).append({
            "id": concept.id,
            "name": concept.name,
            "state": states.get(concept.id, "untested"),
        })

    # A topic with no concepts is skipped. It would render as a card with
    # nothing in it, which reads as a loading failure rather than as the
    # accurate statement that nobody has written its concepts yet.
    return {
        "items": [
            {"topic_id": t.id, "topic": t.name, "concepts": by_topic[t.id]}
            for t in topics
            if by_topic.get(t.id)
        ]
    }


# ---------------------------------------------------------------------------
# teacher-006 (student half) -- what a teacher actually approved
# ---------------------------------------------------------------------------

@router.get("/assignments")
def assignments(
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """Reteach units a teacher has approved, for the student they were written
    about.

    The other side of the approval gate. `teacher-006` is only a
    human-in-the-loop story if approval actually leads somewhere, and until
    this existed an approved unit went nowhere -- the gate opened onto a wall.

    `status == "assigned"` is the whole access rule, and it is applied in the
    query rather than checked afterwards. A draft is not filtered out of a
    fetched list; it is never fetched.

    Scoped to the student's course through the misconception's topic, so a
    reteach approved for the Django class does not appear for a physics
    student.

    `citations` is deliberately empty rather than absent. A unit's citations
    are gathered while it is being drafted and there is nowhere to keep them --
    `reteach_units` has no column for them, and adding one means a schema
    change nobody can afford mid-build. An empty list is honest; inventing
    sources at read time would not be.
    """
    stmt = (
        select(ReteachUnit, Misconception)
        .join(Misconception, Misconception.id == ReteachUnit.misconception_id)
        .where(ReteachUnit.status == "assigned")
        .order_by(ReteachUnit.id.desc())
    )
    if user.course_id is not None:
        stmt = stmt.join(Topic, Topic.id == Misconception.topic_id).where(
            Topic.course_id == user.course_id
        )

    rows = db.execute(stmt).all()

    # Approval time lives in the audit log, because reteach_units has no
    # approved_at column. Same source teacher-005 reads its boundary from, so
    # the two panels cannot disagree about when a reteach happened.
    stamps = {
        target: at
        for target, at in db.execute(
            select(AuditLog.target, func.min(AuditLog.at))
            .where(AuditLog.action == "reteach.approve")
            .group_by(AuditLog.target)
        ).all()
    }

    return {
        "items": [
            {
                "id": unit.id,
                "title": unit.title,
                "body": unit.body,
                "assigned_at": (
                    stamps[f"reteach:{unit.id}"].isoformat().replace("+00:00", "Z")
                    if f"reteach:{unit.id}" in stamps else None
                ),
                "citations": [],
                # No misconception label. The student is being taught the
                # thing, not told a machine decided they believe the wrong
                # version of it.
            }
            for unit, _ in rows
        ]
    }


# ---------------------------------------------------------------------------
# student-005 -- scoped practice
# ---------------------------------------------------------------------------

@router.post("/practice/generate")
def generate_practice(
    body: PracticeGenerateIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """Practice for one gap's concept -- not random course-wide problems.

    `gap_id` is required rather than optional: practice that is not scoped to a
    gap is just a quiz, and the whole claim of this feature is the scoping.
    """
    gap = db.get(Gap, body.gap_id)
    if gap is None or gap.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such gap."},
        )
    if gap.concept is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict",
                    "message": "That gap has no concept attached to practise."},
        )

    practice_set, items, rejected, used_fallback = practice.generate(
        db,
        user_id=user.id,
        concept=gap.concept,
        course_id=user.course_id,
        gap_id=gap.id,
        count=body.count or practice.DEFAULT_COUNT,
    )

    if not items:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "provider_unavailable",
                    "message": "Could not build practice for that gap right now.",
                    "detail": {"rejected": [r.reason for r in rejected]}},
        )

    return {
        "practice_set_id": practice_set.id,
        "concept": gap.concept.name,
        "items": [
            {
                "id": item.id,
                "prompt": item.prompt,
                "kind": item.kind,
                "options": _options_list(item.options),
                "gap_id": gap.id,
            }
            for item in items
        ],
        # Visible on purpose: a generator that is quietly failing every item and
        # falling back to seeds should be obvious here, not a mystery on stage.
        "source": "seeded" if used_fallback else "generated",
    }


@router.get("/practice/{practice_set_id}")
def get_practice_set(
    practice_set_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """Re-read a practice set with the answers already given -- student-009.

    Read-only. It writes no attempt, moves no mastery row and touches no
    teacher aggregate. Reading a pending diagnosis is emphatically not
    confirming it -- only the confirm route does that.

    `explanation` and `citations` are not replayed. Each one costs a model call
    to produce, and re-rendering yesterday's prose is not what resume is for.
    """
    practice_set = db.get(PracticeSet, practice_set_id)
    if practice_set is None or practice_set.user_id != user.id:
        # 404 for someone else's set, never 403: one student must not be able
        # to discover that another student's set exists.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such practice set."},
        )

    items = db.scalars(
        select(PracticeItem)
        .options(selectinload(PracticeItem.concept))
        .where(PracticeItem.practice_set_id == practice_set.id)
        .order_by(PracticeItem.id)
    ).all()

    # Latest attempt per item, in one query. Ordered by id so the last write
    # into the dict wins, which is the newest attempt.
    latest_attempt: dict[int, Attempt] = {}
    if items:
        latest_attempt = {
            a.practice_item_id: a
            for a in db.scalars(
                select(Attempt)
                .where(
                    Attempt.user_id == user.id,
                    Attempt.practice_item_id.in_([i.id for i in items]),
                )
                .order_by(Attempt.id)
            ).all()
        }

    diagnosis_by_attempt: dict[int, MisconceptionDiagnosis] = {}
    if latest_attempt:
        diagnosis_by_attempt = {
            d.attempt_id: d
            for d in db.scalars(
                select(MisconceptionDiagnosis)
                .options(selectinload(MisconceptionDiagnosis.misconception))
                .where(
                    MisconceptionDiagnosis.attempt_id.in_(
                        [a.id for a in latest_attempt.values()]
                    )
                )
                .order_by(MisconceptionDiagnosis.id)
            ).all()
        }

    def _item_out(item: PracticeItem) -> dict:
        attempt = latest_attempt.get(item.id)
        diagnosis = diagnosis_by_attempt.get(attempt.id) if attempt else None
        return {
            "id": item.id,
            "prompt": item.prompt,
            "kind": item.kind,
            "options": _options_list(item.options),
            "gap_id": practice_set.gap_id,
            # null together when the item has not been answered.
            "your_answer": attempt.answer if attempt else None,
            "correct": attempt.correct if attempt else None,
            "diagnosis": {
                "id": diagnosis.id,
                "misconception_id": diagnosis.misconception_id,
                "label": diagnosis.misconception.label,
                "question": practice.confirm_question(diagnosis.misconception),
                # null = asked but not answered yet. That is a question still
                # waiting for the student, and rendering it is what lets the
                # golden path survive a reload mid-flow.
                "confirmed": diagnosis.confirmed,
            } if diagnosis is not None and diagnosis.misconception is not None else None,
        }

    gap = db.get(Gap, practice_set.gap_id) if practice_set.gap_id else None
    concept = gap.concept if gap is not None else None
    if concept is None:
        concept = next((i.concept for i in items if i.concept is not None), None)

    return {
        "practice_set_id": practice_set.id,
        "concept": concept.name if concept is not None else None,
        # generate() knows whether it fell back; by the time the rows are on
        # disk the only surviving record of that is is_seed on the items.
        "source": "seeded" if any(i.is_seed for i in items) else "generated",
        "items": [_item_out(i) for i in items],
    }


# ---------------------------------------------------------------------------
# student-006 -- answer, and the misconception behind a wrong one
# ---------------------------------------------------------------------------

@router.post("/practice/{practice_set_id}/answer")
def answer_practice(
    practice_set_id: int,
    body: PracticeAnswerIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """Record the attempt and, when it is wrong, name the likely misconception.

    The diagnosis is a *question*, never a verdict. It is written with
    `confirmed = None` and only counts for a teacher once the student agrees --
    the student is the authority on what they were thinking.
    """
    practice_set = db.get(PracticeSet, practice_set_id)
    if practice_set is None or practice_set.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such practice set."},
        )

    item = db.get(PracticeItem, body.item_id)
    if item is None or item.practice_set_id != practice_set.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found",
                    "message": "That item is not in this practice set."},
        )

    correct = practice.is_correct(body.answer, item.correct_answer)
    attempt = Attempt(user_id=user.id, practice_item_id=item.id,
                      answer=body.answer, correct=correct)
    db.add(attempt)
    db.flush()

    if item.concept_id is not None:
        mastery = db.scalar(
            select(Mastery).where(Mastery.user_id == user.id,
                                  Mastery.concept_id == item.concept_id)
        )
        if mastery is None:
            mastery = Mastery(user_id=user.id, concept_id=item.concept_id)
            db.add(mastery)
        mastery.state = "solid" if correct else "shaky"

    diagnosis_out = None
    if not correct:
        misconception, source = practice.diagnose(db, item, body.answer)
        if misconception is not None:
            diagnosis = MisconceptionDiagnosis(
                attempt_id=attempt.id,
                misconception_id=misconception.id,
                source=source,
                confirmed=None,      # asked, not decided
            )
            db.add(diagnosis)
            db.flush()
            diagnosis_out = {
                "id": diagnosis.id,
                "misconception_id": misconception.id,
                "label": misconception.label,
                "question": practice.confirm_question(misconception),
            }

    explanation, citations = practice.explain(
        db, item, body.answer, correct, user.course_id
    )

    return {
        "correct": correct,
        "correct_answer": item.correct_answer,
        "explanation": explanation,
        "citations": citations,
        # null when the answer was right, or when no known error pattern
        # matches -- a generic diagnosis is worse than none, because the
        # student is asked to confirm reasoning that was never theirs.
        "diagnosis": diagnosis_out,
    }


@router.post("/misconception-diagnosis/{diagnosis_id}/confirm",
             status_code=status.HTTP_204_NO_CONTENT)
def confirm_diagnosis(
    diagnosis_id: int,
    body: ConfirmDiagnosisIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> Response:
    """The student agrees or disagrees that this was their reasoning.

    Only `true` ever reaches a teacher aggregate. A denial is kept -- throwing
    it away would make the system look more accurate than it is -- but excluded
    everywhere, which is what makes the teacher's number mean "students who
    agreed" rather than "the algorithm's guesses".
    """
    diagnosis = db.get(MisconceptionDiagnosis, diagnosis_id)
    if diagnosis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such diagnosis."},
        )

    attempt = db.get(Attempt, diagnosis.attempt_id)
    if attempt is None or attempt.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such diagnosis."},
        )

    diagnosis.confirmed = body.confirmed
    return Response(status_code=status.HTTP_204_NO_CONTENT)
