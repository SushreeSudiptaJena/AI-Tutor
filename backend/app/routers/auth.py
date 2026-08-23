"""Signup, login, logout, me.

Forgot password has NO route here, deliberately. auth-002 is a UI-only screen
that collects an email and shows confirmation copy; it makes no network call.
Its absence is intentional -- do not add POST /auth/forgot-password.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..deps import current_user
from ..models import Session, User
from ..schemas import LoginIn, PreferencesIn, SignupIn, TokenOut, UserOut
from ..security import hash_password, new_session_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(db: OrmSession, user: User) -> str:
    token = new_session_token()
    db.add(Session(token=token, user_id=user.id))
    db.flush()
    return token


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupIn, db: OrmSession = Depends(get_db)) -> TokenOut:
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict", "message": "That email is already registered."},
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        course_id=body.course_id,
        preferred_language="en",
    )
    db.add(user)
    db.flush()

    return TokenOut(token=_issue_token(db, user), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: OrmSession = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email))

    # Same response whether the email is unknown or the password is wrong.
    # Distinguishing them turns this into an account-enumeration oracle.
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthenticated", "message": "Email or password is incorrect."},
        )

    return TokenOut(token=_issue_token(db, user), user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: User = Depends(current_user),
    db: OrmSession = Depends(get_db),
) -> Response:
    """Delete every session for this user, so logout works across devices."""
    for session in db.scalars(select(Session).where(Session.user_id == user.id)).all():
        db.delete(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me/preferences", response_model=UserOut)
def update_preferences(
    body: PreferencesIn,
    user: User = Depends(current_user),
    db: OrmSession = Depends(get_db),
) -> UserOut:
    user.preferred_language = body.preferred_language
    db.flush()
    return UserOut.model_validate(user)
