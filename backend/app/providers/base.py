"""The provider interface every model call goes through.

No service ever talks to GLM, Gemini, Groq or Sarvam directly. Everything routes
here, which is what makes the disk cache and the fallback chain universal rather
than something each caller has to remember.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class ProviderError(RuntimeError):
    """One provider failed. The chain should try the next one."""

    def __init__(self, provider: str, message: str, *, retryable: bool = True):
        super().__init__(f"{provider}: {message}")
        self.provider = provider
        self.retryable = retryable


class AllProvidersFailed(RuntimeError):
    """Every configured provider failed. Surfaces as 503 provider_unavailable."""

    def __init__(self, attempts: list[tuple[str, str]]):
        detail = "; ".join(f"{name}: {err}" for name, err in attempts)
        super().__init__(f"all providers failed -> {detail}")
        self.attempts = attempts


@dataclass(frozen=True)
class Completion:
    """What every call returns. `provider` and `cached` exist so the demo can
    show on screen which vendor answered and whether it came off disk."""

    text: str
    provider: str
    model: str
    cached: bool = False


@runtime_checkable
class Provider(Protocol):
    name: str
    model: str

    def complete(
        self,
        prompt: str,
        *,
        system: str = "",
        json_schema: dict | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> str:
        """Return the model's text. Raise ProviderError on any failure.

        temperature defaults to 0.0 on purpose: a tutor should give the same
        answer to the same question, and a deterministic model makes the disk
        cache genuinely equivalent to a live call.
        """
        ...
