"""auth-001 tests.

No database and no network, consistent with the rest of the suite:
  * password functions are pure
  * the 401 path is checked before the database is touched
  * authenticated routes are exercised via dependency_overrides with a fake user

The full signup -> login -> logout round trip against the real database is a
manual verification step, recorded in evidence/auth-001/.
"""

import re

import pytest
from fastapi.testclient import TestClient

from app.deps import current_user
from app.main import app
from app.models import User
from app.security import hash_password, new_session_token, verify_password

client = TestClient(app)


# --- password hashing -------------------------------------------------------

def test_hash_is_not_the_plaintext():
    h = hash_password("demo1234")
    assert "demo1234" not in h
    assert h.startswith("pbkdf2_sha256$")


def test_correct_password_verifies():
    assert verify_password("demo1234", hash_password("demo1234"))


def test_wrong_password_does_not_verify():
    assert not verify_password("wrong-password", hash_password("demo1234"))


def test_same_password_hashes_differently_each_time():
    """Random salt: two users with the same password must not share a hash."""
    assert hash_password("demo1234") != hash_password("demo1234")


def test_verify_never_raises_on_a_malformed_hash():
    for bad in ["", "garbage", "pbkdf2_sha256$nope", "$$$", "md5$1$a$b"]:
        assert verify_password("demo1234", bad) is False


def test_seeded_deterministic_salt_still_verifies():
    """seed.py pins the salt so re-seeding is a no-op; that must still verify."""
    h = hash_password("demo1234", salt="a" * 32)
    assert verify_password("demo1234", h)
    assert hash_password("demo1234", salt="a" * 32) == h


def test_session_tokens_are_unique_and_opaque():
    tokens = {new_session_token() for _ in range(50)}
    assert len(tokens) == 50
    # Not a JWT: no dots, nothing decodable inside it.
    assert all("." not in t and len(t) >= 32 for t in tokens)


# --- unauthenticated access (no database touched) ---------------------------

@pytest.mark.parametrize("path", ["/auth/me"])
def test_protected_route_without_a_token_is_401(path):
    r = client.get(path)
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthenticated"


def test_malformed_authorization_header_is_401():
    for header in ["Basic abc", "Bearer", "Bearer    ", "token abc"]:
        r = client.get("/auth/me", headers={"Authorization": header})
        assert r.status_code == 401, header
        assert r.json()["error"]["code"] == "unauthenticated"


# --- error envelope ---------------------------------------------------------

def test_validation_error_uses_the_contract_envelope():
    r = client.post("/auth/signup", json={"email": "not-an-email",
                                          "password": "short", "full_name": ""})
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    # detail carries per-field messages
    assert set(err["detail"]) >= {"email", "password", "full_name"}


# --- authenticated routes, with the database dependency overridden ----------

@pytest.fixture
def as_student():
    user = User(id=7, email="asha@example.edu", password_hash="x",
                full_name="Asha R", role="student", course_id=3,
                preferred_language="en")
    app.dependency_overrides[current_user] = lambda: user
    yield user
    app.dependency_overrides.clear()


def test_me_returns_the_user(as_student):
    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json() == {
        "id": 7, "email": "asha@example.edu", "full_name": "Asha R",
        "role": "student", "course_id": 3, "preferred_language": "en",
        # auth-004 / student-010: enrolment fields exist on every User now,
        # null when unset. batch_id is the COHORT; course_id above is the
        # active subject.
        "university": None, "roll_number": None, "batch_id": None,
    }


def test_me_never_leaks_the_password_hash(as_student):
    body = client.get("/auth/me").json()
    assert "password_hash" not in body
    assert "password" not in body


# ---------------------------------------------------------------------------
# auth-003 -- the role guards, exercised rather than inspected
# ---------------------------------------------------------------------------
#
# test_admin.py and test_teacher.py assert that each route *mentions*
# admin_only / teacher_only in its source. That catches a route written without
# a guard; it cannot catch a guard that does not actually refuse, because it
# never sends a request. These do.
#
# No database: require_role() runs as a dependency, so it raises before the
# handler body executes and nothing reaches Neon.

def _as(role: str, **kw):
    """Sign in as a role, for the duration of a `with` block."""
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        user = User(id=kw.get("id", 1), email=f"{role}@example.edu",
                    password_hash="x", full_name=role.title(), role=role,
                    course_id=kw.get("course_id", 3), preferred_language="en")
        app.dependency_overrides[current_user] = lambda: user
        try:
            yield user
        finally:
            app.dependency_overrides.clear()

    return _ctx()


def _get_routes(prefix: str) -> list[str]:
    """Every GET route under a prefix, with path params filled in.

    GET only, deliberately: a POST would have its body validated too, and a 422
    from an empty body would mask the 403 this is trying to observe.
    """
    # Read the OpenAPI schema, not app.routes: this FastAPI version keeps
    # included routers nested, so app.routes holds an opaque _IncludedRouter
    # rather than the routes themselves -- and a sweep over it silently found
    # nothing at all, which is what the canary test below exists to catch.
    paths = [
        re.sub(r"\{[^}]+\}", "1", path)
        for path, ops in app.openapi()["paths"].items()
        if path.startswith(prefix) and "get" in ops
    ]
    return sorted(set(paths))


def test_there_are_admin_and_teacher_routes_to_guard():
    """If this ever returns nothing, the sweeps below are vacuously passing."""
    assert len(_get_routes("/admin")) >= 5
    assert len(_get_routes("/teacher")) >= 5


def test_a_student_is_forbidden_from_every_admin_route():
    with _as("student"):
        for path in _get_routes("/admin"):
            r = client.get(path)
            assert r.status_code == 403, f"{path} gave {r.status_code} to a student"
            assert r.json()["error"]["code"] == "forbidden", path


def test_a_teacher_is_forbidden_from_every_admin_route():
    """teacher_only admits teachers; nothing under /admin does. Uploading course
    material and rewriting the prerequisite graph are institutional acts."""
    with _as("teacher"):
        for path in _get_routes("/admin"):
            r = client.get(path)
            assert r.status_code == 403, f"{path} gave {r.status_code} to a teacher"


def test_a_student_is_forbidden_from_every_teacher_route():
    with _as("student"):
        for path in _get_routes("/teacher"):
            r = client.get(path)
            assert r.status_code == 403, f"{path} gave {r.status_code} to a student"
            assert r.json()["error"]["code"] == "forbidden", path


def _permits(guard, role: str) -> bool:
    """Does this guard admit `role`? Calls the dependency directly.

    Deliberately NOT over HTTP. A permitted request runs the real handler, and
    the handler talks to Neon -- sweeping fourteen routes as an admin took the
    suite from 9 seconds to over three minutes, for a fact the guard itself can
    answer. The refusal sweeps below stay over HTTP, because a 403 short-
    circuits in the dependency and never reaches the database.
    """
    from fastapi import HTTPException

    user = User(id=1, email=f"{role}@example.edu", password_hash="x",
                full_name=role, role=role, course_id=3, preferred_language="en")
    try:
        return guard(user=user) is user
    except HTTPException:
        return False


def test_each_guard_admits_exactly_the_roles_it_should():
    """A guard that refuses everyone would pass every 403 test above."""
    from app.deps import admin_only, student_only, teacher_only

    assert _permits(admin_only, "admin")
    assert not _permits(admin_only, "teacher")
    assert not _permits(admin_only, "student")

    # teacher_only is require_role("teacher", "admin") -- an admin locked out of
    # the dashboards would be a guard that is merely strict, not correct.
    assert _permits(teacher_only, "teacher")
    assert _permits(teacher_only, "admin")
    assert not _permits(teacher_only, "student")

    assert _permits(student_only, "student")
    assert not _permits(student_only, "teacher")


def test_an_unknown_role_is_admitted_by_nothing():
    from app.deps import admin_only, student_only, teacher_only

    for guard in (admin_only, teacher_only, student_only):
        assert not _permits(guard, "registrar")


def test_forbidden_is_403_and_not_401():
    """The caller IS authenticated, just not permitted. Answering 401 would tell
    a signed-in student to go and sign in again."""
    with _as("student"):
        r = client.get("/admin/courses")
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"
    assert "role" in r.json()["error"]["message"].lower()


def test_an_unauthenticated_caller_gets_401_from_a_role_guarded_route():
    """The other order: no token at all must be 401, not 403 -- 403 would
    confirm the route exists to someone who never identified themselves."""
    for path in ("/admin/courses", "/teacher/misconceptions/heatmap"):
        r = client.get(path)
        assert r.status_code == 401, path
        assert r.json()["error"]["code"] == "unauthenticated", path


def test_every_admin_and_teacher_route_is_guarded_at_all():
    """Not one of them may answer an anonymous caller."""
    for path in _get_routes("/admin") + _get_routes("/teacher"):
        assert client.get(path).status_code == 401, f"{path} answered anonymously"
