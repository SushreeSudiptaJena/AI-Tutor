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
from ..models import AuditLog, Course, CourseTeacher, Session, User
from ..schemas import LoginIn, PreferencesIn, SignupIn, TokenOut, UserOut
from ..security import hash_password, new_session_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(db: OrmSession, user: User) -> str:
    token = new_session_token()
    db.add(Session(token=token, user_id=user.id))
    db.flush()
    return token


# admin-011. The admin's notification bell reads this out of the audit log.
FIRST_LOGIN_ACTION = "teacher.first_login"


def _note_first_login(db: OrmSession, user: User) -> None:
    """Record, exactly once, that an admin-issued teacher account was used.

    **This is not a login log, and it must not become one.** models.py forbids a
    last-seen column and means it -- so there is no column here at all: the
    existence of the row IS the record, which is also why this can only ever
    fire once. Students and admins are never recorded; only teachers, because
    only a teacher account is born from an admin generating a password and
    handing it over (POST /admin/courses/{id}/teachers shows it exactly once).
    Whether that handoff worked is the one thing the admin cannot otherwise find
    out, and it is the whole reason this row exists.

    `action` is indexed, so the "have we written this already" check reads a
    handful of rows, and a teacher logs in rarely enough for that to be free.

    Wrapped in a savepoint: a notification is never worth failing a login over.
    Without one, a failed INSERT would poison the session and take the token
    that was just issued down with it -- locking a teacher out of the demo over
    a bell.
    """
    if user.role != "teacher":
        return

    target = f"user:{user.id}"
    try:
        with db.begin_nested():
            already = db.scalar(
                select(AuditLog.id)
                .where(AuditLog.action == FIRST_LOGIN_ACTION,
                       AuditLog.target == target)
                .limit(1)
            )
            if already is not None:
                return

            # The subjects they were assigned to at this moment. Captured into
            # the row rather than looked up at read time, because an unassign
            # afterwards must not rewrite history the admin already read.
            codes = list(db.scalars(
                select(Course.code)
                .join(CourseTeacher, CourseTeacher.course_id == Course.id)
                .where(CourseTeacher.user_id == user.id)
                .order_by(Course.code)
            ).all())

            db.add(AuditLog(
                actor_id=user.id,
                action=FIRST_LOGIN_ACTION,
                target=target,
                detail={"email": user.email, "name": user.full_name,
                        "courses": codes},
            ))
            db.flush()
    except Exception:  # noqa: BLE001 -- see docstring: the login still wins
        pass


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
        # auth-004: students only. Teacher accounts are issued by an admin
        # (POST /admin/courses/{id}/teachers) with a shareable password;
        # there is no self-serve teacher signup any more.
        role="student",
        course_id=None,
        preferred_language="en",
        university=(body.university or "").strip()[:200] or None,
        roll_number=(body.roll_number or "").strip()[:60] or None,
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

    token = _issue_token(db, user)
    # After the token, never before: the savepoint inside means a failure here
    # cannot roll back the session row that was just written.
    _note_first_login(db, user)
    return TokenOut(token=token, user=UserOut.model_validate(user))


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
