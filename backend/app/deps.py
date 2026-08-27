"""Shared FastAPI dependencies.

`current_user` is the gate on every protected route. Written once here and
Depends()-ed everywhere, so there is exactly one place that decides whether a
request is authenticated.
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from .db import get_db
from .models import Session, User


def _unauthenticated(message: str = "Not authenticated.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "unauthenticated", "message": message},
    )


def current_user(
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
    db: OrmSession = Depends(get_db),
) -> User:
    """Resolve `Authorization: Bearer <token>` to a User, or 401.

    The header is checked before the database is touched, so an unauthenticated
    request costs no query -- which is also why the test suite can exercise the
    401 path with no database at all.

    `?token=` is accepted as a fallback for ONE reason (teacher-010): a plain
    `<a href>` or a browser download cannot send a header, and the material
    library's View/Save links are ordinary links on purpose. It is the same
    opaque session token, so it grants nothing extra -- but it does end up in
    browser history, so prefer the header everywhere it is possible.
    """
    if not authorization and token and token.strip():
        authorization = f"Bearer {token.strip()}"

    if not authorization:
        raise _unauthenticated("Missing Authorization header.")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise _unauthenticated("Expected 'Authorization: Bearer <token>'.")

    # One round trip, not two. This runs on every authenticated request, and the
    # database is remote -- a second lookup for the User cost a whole network
    # round trip (~130-450ms measured against Neon) on literally every call.
    user = db.scalar(
        select(User)
        .join(Session, Session.user_id == User.id)
        .where(Session.token == token.strip())
    )
    if user is None:
        # Covers an unknown token, one invalidated by logout, and a session
        # whose user is gone. Same message for all three -- distinguishing them
        # tells an attacker which is which.
        raise _unauthenticated("Invalid or expired token.")
    return user


def require_role(*roles: str):
    """Route guard: `Depends(require_role("teacher", "admin"))`.

    403, not 401 -- the caller is authenticated, just not permitted.
    """

    def _guard(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "forbidden",
                    "message": f"This route requires role: {', '.join(roles)}.",
                },
            )
        return user

    return _guard


# Convenience aliases used by the routers.
student_only = require_role("student")
teacher_only = require_role("teacher", "admin")
admin_only = require_role("admin")
