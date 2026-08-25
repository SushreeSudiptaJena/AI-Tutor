"""infra-004 tests. No network, no database.

The HTTP providers are exercised against fakes; the real vendors are checked by
backend/scripts/bench_providers.py and recorded in evidence/infra-004/.
"""

import inspect
import json

import pytest

from app.providers import cache, complete
from app.providers.base import AllProvidersFailed, Completion, ProviderError
from app.providers.http_providers import _strip_fences, _strip_reasoning
from app.providers.mock import MockProvider


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Point the cache at a temp dir so tests never touch the real one."""
    from app import config

    monkeypatch.setattr(config, "LLM_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "LLM_CACHE_ENABLED", True)
    yield


# --- cache ------------------------------------------------------------------

def test_cache_key_is_stable_for_identical_input():
    a = cache.make_key("q", system="s")
    b = cache.make_key("q", system="s")
    assert a == b and len(a) == 64


def test_cache_key_changes_with_prompt_system_and_schema():
    base = cache.make_key("q", system="s")
    assert cache.make_key("q2", system="s") != base
    assert cache.make_key("q", system="s2") != base
    assert cache.make_key("q", system="s", json_schema={"type": "object"}) != base


def test_cache_key_excludes_provider_and_model():
    """Deliberate: rehearse on one vendor, fall back to another mid-demo, and
    the cached answer must still be reused."""
    import inspect

    src = inspect.getsource(cache.make_key)
    assert "model" not in src and "provider" not in src


def test_cache_round_trip():
    key = cache.make_key("hello")
    assert cache.get(key) is None
    cache.put(key, text="world", provider="p", model="m")
    hit = cache.get(key)
    assert hit["text"] == "world" and hit["provider"] == "p"


def test_corrupt_cache_entry_is_discarded_not_raised():
    key = cache.make_key("hello")
    cache.put(key, text="world", provider="p", model="m")
    (cache.cache_dir() / f"{key}.json").write_text("{ this is not json", encoding="utf-8")
    assert cache.get(key) is None  # and did not raise


def test_cache_can_be_disabled(monkeypatch):
    from app import config

    monkeypatch.setattr(config, "LLM_CACHE_ENABLED", False)
    key = cache.make_key("x")
    cache.put(key, text="y", provider="p", model="m")
    assert cache.get(key) is None


# --- reasoning-model handling ----------------------------------------------

def test_inline_think_tags_are_stripped():
    assert _strip_reasoning("<think>reasoning here</think>Answer") == "Answer"
    assert _strip_reasoning("<think>a\nb</think>  Answer  ") == "Answer"
    assert _strip_reasoning("no tags") == "no tags"


def test_json_fences_are_stripped():
    assert _strip_fences('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _strip_fences('{"a": 1}') == '{"a": 1}'


# --- mock provider ----------------------------------------------------------

def test_mock_returns_prose_without_a_schema():
    out = MockProvider().complete("Explain constant velocity")
    assert isinstance(out, str) and len(out) > 40


def test_mock_returns_valid_json_for_a_schema():
    schema = {"type": "object", "properties": {"entailment": {"type": "number"}}}
    out = MockProvider().complete("how supported is this?", json_schema=schema)
    assert 0.0 <= json.loads(out)["entailment"] <= 1.0


def test_mock_classifies_solve_intent_for_the_guardrail():
    schema = {"type": "object", "properties": {"intent": {"type": "string"}}}
    solve = json.loads(MockProvider().complete("Solve Q3 for me", json_schema=schema))
    understand = json.loads(
        MockProvider().complete("Why does Q3 use momentum?", json_schema=schema)
    )
    assert solve["intent"] == "solve"
    assert understand["intent"] == "understand"


# --- the chain --------------------------------------------------------------

class _Boom:
    name = "boom"
    model = "explodes"

    def complete(self, prompt, **kw):
        raise ProviderError("boom", "simulated outage")


class _Weird:
    name = "weird"
    model = "raises-typeerror"

    def complete(self, prompt, **kw):
        raise TypeError("not a ProviderError at all")


class _Fine:
    name = "fine"
    model = "works"

    def complete(self, prompt, **kw):
        return "recovered"


def test_chain_falls_through_to_the_next_provider(monkeypatch):
    import app.providers as providers

    monkeypatch.setattr(providers, "chain", lambda: [_Boom(), _Fine()])
    r = complete("anything")
    assert r.text == "recovered" and r.provider == "fine"


def test_an_unexpected_exception_does_not_break_the_chain(monkeypatch):
    """A provider raising something other than ProviderError must not take down
    the request - it is just another dead vendor."""
    import app.providers as providers

    monkeypatch.setattr(providers, "chain", lambda: [_Weird(), _Fine()])
    assert complete("anything").text == "recovered"


def test_empty_chain_raises_all_providers_failed(monkeypatch):
    import app.providers as providers

    monkeypatch.setattr(providers, "chain", lambda: [_Boom()])
    with pytest.raises(AllProvidersFailed):
        complete("anything")


def test_second_identical_call_is_served_from_cache(monkeypatch):
    import app.providers as providers

    calls = {"n": 0}

    class Counting:
        name, model = "counting", "c1"

        def complete(self, prompt, **kw):
            calls["n"] += 1
            return "answer"

    monkeypatch.setattr(providers, "chain", lambda: [Counting()])
    first = complete("same question")
    second = complete("same question")
    assert calls["n"] == 1
    assert first.cached is False and second.cached is True
    assert first.text == second.text


def test_mock_only_chain_never_fails(monkeypatch):
    """PROVIDER=mock must work with no keys and no network."""
    from app import config

    monkeypatch.setattr(config, "PROVIDER", "mock")
    r = complete("explain something", use_cache=False)
    assert isinstance(r, Completion) and r.provider == "mock" and r.text


def hp_mod():
    from app.providers import http_providers

    return http_providers


# ---------------------------------------------------------------------------
# infra-004 -- GLM through the coding plan, last in the chain
# ---------------------------------------------------------------------------

def test_glm_coding_is_the_last_real_vendor_before_mock():
    """It is the only provider on a paid subscription rather than a free tier,
    so it is the likeliest to answer when everything else is rate-limited --
    but it is slow, so it must not lead."""
    from app.providers import chain_names

    names = [n.split(":")[0] for n in chain_names()]
    assert "glm-coding" in names, names
    assert names[-1] == "mock", names
    assert names[-2] == "glm-coding", names


def test_the_coding_plan_uses_a_different_endpoint_than_pay_as_you_go():
    """Same key, two pools. Every paid model on /api/paas/v4 answers
    'insufficient balance'; the Anthropic-shaped endpoint answers 200. Pointing
    this at the OpenAI-shaped URL would silently reinstate the dead path."""
    from app.providers.http_providers import glm, glm_coding

    assert "/api/anthropic" in glm_coding().base_url
    assert "/api/paas/v4" in glm().base_url
    assert glm_coding().base_url != glm().base_url


def test_glm_coding_gets_a_longer_read_budget_than_the_shared_one():
    """It measured 17-23s on a cold call against an 18s shared budget. A
    provider that always times out is worse than one that is absent: it costs
    the whole budget before the chain moves on."""
    from app.providers import http_providers as hp

    assert hp.SLOW_TIMEOUT.read > hp.TIMEOUT.read
    assert "SLOW_TIMEOUT" in inspect.getsource(hp.AnthropicCompatProvider.complete)


def test_the_anthropic_provider_reads_only_visible_text_blocks():
    """A thinking model emits `thinking` blocks beside `text` ones. Joining all
    of them would put the model's reasoning in front of a student."""
    source = inspect.getsource(hp_mod().AnthropicCompatProvider.complete)
    assert 'b.get("type") == "text"' in source


def test_the_anthropic_provider_sends_system_beside_the_messages():
    """Anthropic's shape has no system ROLE; a system message smuggled into
    `messages` is either ignored or rejected."""
    source = inspect.getsource(hp_mod().AnthropicCompatProvider.complete)
    assert 'body["system"] = system' in source
    assert '"role": "system"' not in source


def test_a_failing_chain_reaches_glm_coding_before_mock(monkeypatch):
    """The whole point of its position: it must actually be tried."""
    from app.providers import chain
    from app.providers.base import ProviderError

    tried = []
    providers = chain()
    for p in providers:
        if p.name == "mock":
            continue

        def fail(*a, _n=p.name, **kw):
            tried.append(_n)
            if _n == "glm-coding":
                return "reached"
            raise ProviderError(_n, "simulated outage")

        monkeypatch.setattr(p, "complete", fail)

    for p in providers:
        try:
            out = p.complete("x")
        except ProviderError:
            continue
        assert out == "reached"
        break
    assert tried[-1] == "glm-coding", tried
    assert "glm-coding" in tried
