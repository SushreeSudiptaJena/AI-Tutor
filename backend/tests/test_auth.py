"""auth-001 tests.

No database and no network, consistent with the rest of the suite:
  * password functions are pure
  * the 401 path is checked before the database is touched
  * authenticated routes are exercised via dependency_overrides with a fake user

The full signup -> login -> logout round trip against the real database is a
manual verification step, recorded in evidence/auth-001/.
"""

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
    }


def test_me_never_leaks_the_password_hash(as_student):
    body = client.get("/auth/me").json()
    assert "password_hash" not in body
    assert "password" not in body
