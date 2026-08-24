"""POST /tutor/ask -- rag-003.

All three outcomes are `200`. A refusal is a successful, correct response, not
an error: returning 4xx would make the frontend's error path render it, and the
whole point is that the student reads the refusal.

The graded-work guardrail (rag-004) attaches here and **only** here. It is not
in the shared service, because a gap lesson is driven by a concept rather than
typed text, so a guardrail refusal there could only ever be a false positive.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..deps import current_user
from ..models import User
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
    )
