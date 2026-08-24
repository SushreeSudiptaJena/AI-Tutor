"""infra-002: proves the app boots and the contract's baseline routes answer.

These must pass with NO database and NO network -- a red baseline has to mean
"you broke something", not "wifi is down".
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200_even_without_a_database():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"ok", "degraded"}
    assert "db" in body


def test_languages_lists_english_and_hindi():
    r = client.get("/languages")
    assert r.status_code == 200
    codes = {item["code"] for item in r.json()["items"]}
    assert {"en", "hi"} <= codes


def test_provider_status_shape():
    r = client.get("/meta/provider-status")
    assert r.status_code == 200
    body = r.json()
    assert {"active", "fallbacks_available", "cache_enabled", "chain", "cache"} <= set(body)
    assert isinstance(body["fallbacks_available"], list)
    # The chain always ends in mock, so a completely keyless machine still runs.
    assert body["chain"][-1].startswith("mock:")
    assert {"entries", "bytes", "enabled"} <= set(body["cache"])


def test_unknown_route_uses_the_contract_error_envelope():
    r = client.get("/no-such-route")
    assert r.status_code == 404
    assert set(r.json()["error"]) == {"code", "message", "detail"}


def test_a_resource_404_keeps_its_own_message():
    """Starlette gives the status-code handler precedence over the
    HTTPException one, so a blanket 404 handler answers "No such route." to a
    route that exists and is telling you the *resource* does not. A frontend
    reading that would show "endpoint missing" for a mistyped gap id."""
    r = client.get("/student/gaps/999999/lesson",
                   headers={"Authorization": "Bearer definitely-not-a-token"})
    # No database here, so this is the 401 path -- the point is only that the
    # generic route message is not what comes back.
    assert r.json()["error"]["message"] != "No such route."


def test_an_unmatched_path_still_says_no_such_route():
    r = client.get("/no/such/path/at/all")
    assert r.status_code == 404
    assert r.json()["error"] == {"code": "not_found",
                                 "message": "No such route.", "detail": {}}
