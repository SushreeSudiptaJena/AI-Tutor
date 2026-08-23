"""The single entry point for every model call.

    from app.providers import complete
    result = complete("Explain vector components", system=RULES)
    result.text, result.provider, result.cached

Order of operations:

    cache lookup  ->  hit? return immediately
                  ->  miss? walk the provider chain, first success wins
                  ->  store and return

The chain is GLM -> Gemini -> Groq -> Groq(alternate model) -> mock,
deliberately across DIFFERENT vendors so one outage or rate limit cannot take
out its own backup. mock is last, so the worst case is "generic answers", never
"the app is broken" in front of judges.
"""

from __future__ import annotations

from .. import config
from . import cache
from .base import AllProvidersFailed, Completion, Provider, ProviderError
from .http_providers import gemini, glm, groq
from .mock import MockProvider

__all__ = [
    "complete", "chain", "chain_names", "Completion",
    "Provider", "ProviderError", "AllProvidersFailed", "cache",
]


def chain() -> list[Provider]:
    """Providers to try, in order. Unconfigured ones are dropped."""
    primary = (config.PROVIDER or "glm").lower()

    if primary == "mock":
        return [MockProvider()]

    builders = {"glm": glm, "gemini": gemini, "groq": groq}

    # Ordered by MEASURED median latency on this account, not by preference.
    # A judge asking a novel question waits for the first uncached call, so the
    # fastest working vendor goes first. Re-measure with
    # backend/scripts/bench_providers.py if keys or models change.
    #   groq   openai/gpt-oss-120b    ~1.3 s
    #   groq   qwen/qwen3.6-27b       ~2.4 s
    #   gemini gemini-3.6-flash       ~6.5 s
    #   glm    glm-4.5-flash         ~21.7 s   (works, but far too slow to lead)
    BY_SPEED = ("groq", "gemini", "glm")
    order = [primary] + [n for n in BY_SPEED if n != primary]

    out: list[Provider] = []
    for name in order:
        build = builders.get(name)
        if build is None:
            continue
        p = build()
        if getattr(p, "configured", True):
            out.append(p)

    # A second Groq model is a cheap extra life: a per-model rate limit is far
    # more common than a whole account being cut off.
    alt = config.FALLBACK_MODEL_GROQ_ALTERNATIVE
    if alt and config.FALLBACK_API_KEY_GROQ:
        out.append(groq(alt))

    out.append(MockProvider())  # last resort, never fails
    return out


def chain_names() -> list[str]:
    return [f"{p.name}:{p.model}" for p in chain()]


def complete(
    prompt: str,
    *,
    system: str = "",
    json_schema: dict | None = None,
    temperature: float = 0.0,
    max_tokens: int = 2048,
    use_cache: bool = True,
) -> Completion:
    """Run a prompt through the cache and the provider chain."""
    key = cache.make_key(prompt, system=system, json_schema=json_schema)

    if use_cache:
        hit = cache.get(key)
        if hit is not None:
            return Completion(
                text=hit["text"],
                provider=hit.get("provider", "cache"),
                model=hit.get("model", ""),
                cached=True,
            )

    attempts: list[tuple[str, str]] = []
    for provider in chain():
        try:
            text = provider.complete(
                prompt,
                system=system,
                json_schema=json_schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except ProviderError as exc:
            attempts.append((provider.name, str(exc)))
            continue
        except Exception as exc:  # noqa: BLE001 - a broken provider must not
            attempts.append((provider.name, f"unexpected {type(exc).__name__}: {exc}"))
            continue          # take down the request; try the next vendor

        if use_cache:
            cache.put(key, text=text, provider=provider.name, model=provider.model)
        return Completion(text=text, provider=provider.name, model=provider.model)

    # MockProvider never raises, so reaching here means the chain was empty.
    raise AllProvidersFailed(attempts)
