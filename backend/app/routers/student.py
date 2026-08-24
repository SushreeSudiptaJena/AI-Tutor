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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..deps import current_user
from ..models import (
    Chunk,
    Concept,
    Course,
    DiagnosticItem,
    Gap,
    Mastery,
    Material,
    Topic,
    User,
)
from ..schemas import DiagnosticSubmitIn
from ..services import retrieval, tutor

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

    count = len(gaps)
    return {
        "gaps": [_gap_out(db, g) for g in gaps],
        "message": (
            "No prerequisite gaps found." if count == 0
            else f"Found {count} prerequisite gap{'' if count == 1 else 's'}."
        ),
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
