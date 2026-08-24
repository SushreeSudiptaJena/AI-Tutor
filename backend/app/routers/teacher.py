"""Teacher routes -- teacher-001 and teacher-004.

Two rules, and they are the same rule twice:

* **Every response here is anonymised.** No student id, no name, no email, in
  any field. Not "not rendered by the frontend" -- not present in the payload.
  The heatmap joins through attempts to reach a diagnosis and deliberately
  drops the student on the way; `uncertainty_flags` never had a `user_id`
  column to drop.

* **Only confirmed diagnoses count.** `confirmed` is three-state: `None` means
  the student was asked and has not answered, `False` means they disagreed.
  Only `True` is aggregated. That is what makes the number on a teacher's
  screen mean "students who agreed this was their reasoning" rather than "times
  the algorithm guessed".

Denied diagnoses are kept, not deleted. Throwing them away would make the
system look more accurate than it is.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..deps import teacher_only
from ..models import (
    Attempt,
    Misconception,
    MisconceptionDiagnosis,
    PracticeItem,
    Topic,
    UncertaintyFlag,
    User,
)
from ..schemas import ResolveFlagIn

router = APIRouter(prefix="/teacher", tags=["teacher"])


def _class_size(db: OrmSession, course_id: int | None) -> int:
    stmt = select(func.count()).select_from(User).where(User.role == "student")
    if course_id is not None:
        stmt = stmt.where(User.course_id == course_id)
    return int(db.scalar(stmt) or 0)


# ---------------------------------------------------------------------------
# teacher-001 -- the misconception heatmap
# ---------------------------------------------------------------------------

@router.get("/misconceptions/heatmap")
def heatmap(
    course_id: int | None = None,
    topic_id: int | None = None,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """The class's most common confirmed wrong mental models, ranked.

    Polled by the frontend on an interval -- there are no websockets anywhere
    in this build. It is a plain aggregate query, so "live" costs nothing: a
    student confirming a diagnosis on another laptop changes the number on the
    next poll.
    """
    course_id = course_id if course_id is not None else user.course_id

    counts = (
        select(
            MisconceptionDiagnosis.misconception_id.label("misconception_id"),
            func.count().label("confirmed_count"),
            func.max(MisconceptionDiagnosis.at).label("latest"),
        )
        .join(Attempt, Attempt.id == MisconceptionDiagnosis.attempt_id)
        .join(PracticeItem, PracticeItem.id == Attempt.practice_item_id)
        .where(MisconceptionDiagnosis.confirmed.is_(True))
        .group_by(MisconceptionDiagnosis.misconception_id)
    )
    # The join above passes through `attempts`, which is the only place a
    # student id exists in this query -- and it is grouped away rather than
    # selected. There is no field here for a name to appear in.

    counts = counts.subquery()

    stmt = (
        select(Misconception, counts.c.confirmed_count, counts.c.latest)
        .join(counts, counts.c.misconception_id == Misconception.id)
        .order_by(counts.c.confirmed_count.desc(), Misconception.id)
    )

    # Scoped to the course, the same way retrieval is. Several courses'
    # misconceptions share this table, and an unscoped heatmap shows a physics
    # teacher the Django class's numbers -- which does not look like a bug, it
    # looks like a surprising result. A misconception with no topic is excluded
    # here, because there is nothing to scope it by.
    if course_id is not None:
        stmt = stmt.join(Topic, Topic.id == Misconception.topic_id).where(
            Topic.course_id == course_id
        )
    if topic_id is not None:
        stmt = stmt.where(Misconception.topic_id == topic_id)

    rows = db.execute(stmt).all()
    size = _class_size(db, course_id)

    topic_name = None
    if topic_id is not None:
        topic = db.get(Topic, topic_id)
        topic_name = topic.name if topic else None

    latest = max((r[2] for r in rows if r[2] is not None), default=None)

    return {
        "topic": topic_name,
        "class_size": size,
        "updated_at": latest.isoformat().replace("+00:00", "Z") if latest else None,
        "items": [
            {
                "misconception_id": m.id,
                "label": m.label,
                "confirmed_count": int(count),
                # Share of the class, not of the diagnoses: "11 of 40 students"
                # is what a teacher acts on.
                "share": round(int(count) / size, 4) if size else 0.0,
                "problem_type": m.problem_type,
            }
            for m, count, _ in rows
        ],
    }


# ---------------------------------------------------------------------------
# teacher-004 -- uncertainty flags
# ---------------------------------------------------------------------------

@router.get("/uncertainty-flags")
def uncertainty_flags(
    status_filter: str = "open",
    limit: int = 50,
    offset: int = 0,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """What the tutor refused to answer, for a human to look at.

    This panel is populated entirely by rag-003 and by gap lessons that could
    not be taught. Nothing writes to it on the teacher's behalf -- one feature,
    two dashboards.

    `alignment_percent` is derived here rather than stored, so it can never
    disagree with the score the student was shown.
    """
    stmt = select(UncertaintyFlag)
    if status_filter and status_filter != "all":
        stmt = stmt.where(UncertaintyFlag.status == status_filter)

    total = int(db.scalar(
        select(func.count()).select_from(stmt.subquery())
    ) or 0)

    rows = db.scalars(
        stmt.order_by(UncertaintyFlag.occurred_at.desc())
        .limit(max(1, min(limit, 200)))
        .offset(max(0, offset))
    ).all()

    return {
        "items": [
            {
                "id": f.id,
                "question": f.question,
                "alignment_percent": round((f.alignment_score or 0.0) * 100),
                "reason": f.reason,
                "topic_id": f.topic_id,
                "occurred_at": f.occurred_at.isoformat().replace("+00:00", "Z")
                if f.occurred_at else None,
                "status": f.status,
                # No student id, because the row never had one. See
                # models.UncertaintyFlag -- you cannot leak what you never
                # stored.
            }
            for f in rows
        ],
        "total": total,
    }


@router.post("/uncertainty-flags/{flag_id}/resolve",
             status_code=status.HTTP_204_NO_CONTENT)
def resolve_flag(
    flag_id: int,
    body: ResolveFlagIn | None = None,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> Response:
    """Mark a flag dealt with. The note is accepted and deliberately not
    stored -- there is no column for it, and inventing one to hold free text
    nobody reads is not worth a migration during a hackathon."""
    flag = db.get(UncertaintyFlag, flag_id)
    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such flag."},
        )
    flag.status = "resolved"
    return Response(status_code=status.HTTP_204_NO_CONTENT)
