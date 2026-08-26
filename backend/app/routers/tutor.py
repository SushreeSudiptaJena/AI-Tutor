"""POST /tutor/ask -- rag-003.

All three outcomes are `200`. A refusal is a successful, correct response, not
an error: returning 4xx would make the frontend's error path render it, and the
whole point is that the student reads the refusal.

The graded-work guardrail (rag-004) attaches here and **only** here. It is not
in the shared service, because a gap lesson is driven by a concept rather than
typed text, so a guardrail refusal there could only ever be a false positive.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..deps import current_user
from ..models import TutorMessage, User
from ..schemas import TutorAskIn
from ..services import tutor

router = APIRouter(prefix="/tutor", tags=["tutor"])


@router.post("/ask")
def ask(
    body: TutorAskIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """Ask a free-form question. Returns a `TutorResponse`.

    The course comes from the signed-in user, never from the request: a student
    must not be able to ask against another course's material by changing a
    number in the body.
    """
    if user.course_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "bad_request",
                "message": "Your account is not enrolled in a course, so there is "
                           "no approved material to answer from.",
            },
        )

    return tutor.ask(
        db,
        body.question,
        course_id=user.course_id,
        language=body.language or user.preferred_language,
        topic_id=body.topic_id,
        user_id=user.id,
    )


@router.get("/history")
def history(
    limit: int = Query(100, ge=1, le=200),
    db: OrmSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    """The signed-in student's own Ask Tutor transcript, oldest first.

    Scope comes from the token, never from the query string: one student must
    not read another's conversation by editing a number. `limit` caps the
    pair count; the response may hold up to twice that many rows because every
    ask writes a student turn and a tutor turn.
    """
    rows = db.scalars(
        select(TutorMessage)
        .where(TutorMessage.user_id == user.id)
        .order_by(TutorMessage.id.desc())
        .limit(limit * 2)
    ).all()

    items = [
        {
            "id": m.id,
            "role": m.role,
            "text": m.text,
            "response": m.response,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in reversed(rows)
    ]
    return {"items": items}
