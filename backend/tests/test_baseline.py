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
    assert set(body) == {"active", "fallbacks_available", "cache_enabled"}
    assert isinstance(body["fallbacks_available"], list)


def test_unknown_route_uses_the_contract_error_envelope():
    r = client.get("/no-such-route")
    assert r.status_code == 404
    assert set(r.json()["error"]) == {"code", "message", "detail"}
