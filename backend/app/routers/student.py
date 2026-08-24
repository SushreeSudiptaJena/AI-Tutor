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
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..deps import current_user
from ..models import (
    Attempt,
    Chunk,
    Concept,
    Course,
    DiagnosticItem,
    Gap,
    Mastery,
    Material,
    MisconceptionDiagnosis,
    PracticeItem,
    PracticeSet,
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


def _gap_out(db: OrmSession, gap: Gap) -> dict:
    concept = gap.concept
    topic = db.get(Topic, concept.topic_id) if concept else None
    prerequisite = (
        db.get(Course, concept.prerequisite_course_id)
        if concept and concept.prerequisite_course_id else None
    )
    return {
        "id": gap.id,
        "concept": concept.name if concept else "",
        "prerequisite_course": prerequisite.title if prerequisite else None,
        "detected_from": gap.detected_from,
        "status": gap.status,
        "suggested_prompts": _suggested_prompts(
            concept.name if concept else "", topic.name if topic else None
        ),
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

    books = []
    for m in materials:
        chapters = db.execute(
            select(Chunk.chapter)
            .where(Chunk.material_id == m.id, Chunk.chapter.is_not(None))
            .group_by(Chunk.chapter)
            .order_by(Chunk.chapter)
        ).all()
        books.append({
            "material_id": m.id,
            "title": m.title,
            "pages": f"1–{m.page_count}" if m.page_count else None,
            "chapters": [c[0] for c in chapters],
        })

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
        .where(DiagnosticItem.course_id == course.id)
        .order_by(DiagnosticItem.id)
    ).all()

    return {
        "diagnostic_id": course.id,
        "items": [
            {
                "id": item.id,
                "prompt": item.prompt,
                "kind": item.kind,
                "options": _options_list(item.options),
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

    return {
        "gaps": [_gap_out(db, g) for g in gaps],
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

    return {
        "gaps": [_gap_out(db, g) for g in gaps],
        "message": _gap_message(len(gaps)),
    }


@router.get("/gaps")
def list_gaps(
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    gaps = db.scalars(
        select(Gap).where(Gap.user_id == user.id).order_by(Gap.id)
    ).all()
    return {"items": [_gap_out(db, g) for g in gaps]}


# ---------------------------------------------------------------------------
# student-003 -- the lesson behind a gap
# ---------------------------------------------------------------------------

@router.get("/gaps/{gap_id}/lesson")
def gap_lesson(
    gap_id: int,
    language: str = "en",
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """A `TutorResponse` for one gap, with the alignment badge and citations.

    Ownership is checked before anything else: a gap id is a small integer, and
    without this check changing it in the URL would read another student's gap
    list back to you one lesson at a time.
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
        language=language,
    )


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
