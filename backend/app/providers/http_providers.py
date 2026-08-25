"""GLM, Groq and Gemini.

GLM (Zhipu) and Groq both expose an OpenAI-compatible chat/completions endpoint,
so they share one implementation and differ only in URL, key and model. Gemini
uses its own request shape and needs its own.

Every failure becomes a ProviderError so the chain moves on to the next vendor.
Nothing here retries internally -- the chain is the retry, and retrying inside a
provider just delays the fallback while a judge watches a spinner.
"""

from __future__ import annotations

import json
import re

import httpx

from .. import config
from .base import ProviderError

# A read timeout is the budget for ONE vendor, and the chain is five deep. At
# read=45 a single rate-limited provider held a click for 45 seconds before the
# fallback was even tried, and two of them outlasted any judge's patience. Our
# real calls answer in 1-3s, so 18s is already ~6x the observed worst case: it
# still tolerates a slow-but-working vendor and fails over from a dead one fast
# enough that the chain reads as resilience rather than as a hang.
TIMEOUT = httpx.Timeout(connect=5.0, read=18.0, write=10.0, pool=5.0)


def _schema_instruction(json_schema: dict | None) -> str:
    if not json_schema:
        return ""
    return (
        "\n\nReturn ONLY valid JSON matching this schema. No prose, no markdown "
        "fences, no explanation outside the JSON.\n"
        + json.dumps(json_schema, indent=2)
    )


# Current-generation models are reasoning models: they spend part of the output
# budget on hidden thinking before producing any visible text. Measured on
# gemini-3.6-flash, a trivial prompt burned 104 thought tokens - so a small
# max_tokens returns finishReason=MAX_TOKENS with completely EMPTY content and
# no error. Budget generously; this is not a knob to trim.
DEFAULT_MAX_TOKENS = 2048
MIN_MAX_TOKENS = 1024

# The header Anthropic-compatible endpoints require. A constant, not a magic
# string, because a wrong value fails as a 400 that reads like a bad key.
ANTHROPIC_VERSION = "2023-06-01"

# GLM through the coding plan measured 17-23s on a trivial prompt -- it is a
# reasoning model on a subscription endpoint, not a fast one. The 18s shared
# read budget would time it out MOST of the time, and a provider that always
# times out is worse than one that is absent: it costs 18s before the chain
# moves on. It is last, so a longer budget here delays nothing else.
SLOW_TIMEOUT = httpx.Timeout(connect=5.0, read=40.0, write=10.0, pool=5.0)

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _strip_reasoning(text: str) -> str:
    """Some models emit their chain of thought inline in <think> tags."""
    return _THINK_RE.sub("", text).strip()


def _strip_fences(text: str) -> str:
    """Models wrap JSON in ```json fences even when told not to."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1] if "\n" in t else t
        if t.endswith("```"):
            t = t[: -3]
        if t.lstrip().startswith("json"):
            t = t.lstrip()[4:]
    return t.strip()


class OpenAICompatProvider:
    """Works for any vendor exposing POST /chat/completions in OpenAI's shape."""

    def __init__(self, *, name: str, base_url: str, api_key: str, model: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    def complete(
        self,
        prompt: str,
        *,
        system: str = "",
        json_schema: dict | None = None,
        temperature: float = 0.0,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        if not self.configured:
            raise ProviderError(self.name, "no API key or model configured", retryable=False)

        max_tokens = max(max_tokens, MIN_MAX_TOKENS)  # leave room for reasoning
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt + _schema_instruction(json_schema)})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_schema:
            payload["response_format"] = {"type": "json_object"}

        try:
            r = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"},
                json=payload,
                timeout=TIMEOUT,
            )
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"network error: {type(exc).__name__}") from exc

        if r.status_code != 200:
            raise ProviderError(self.name, f"HTTP {r.status_code}: {r.text[:180]}")

        try:
            text = r.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(self.name, f"unexpected response shape: {r.text[:180]}") from exc

        text = _strip_reasoning(text or "")
        if not text:
            raise ProviderError(
                self.name,
                "empty response after reasoning tokens - raise max_tokens",
            )
        return _strip_fences(text) if json_schema else text


class GeminiProvider:
    """Google Generative Language API."""

    def __init__(self, *, api_key: str, model: str):
        self.name = "gemini"
        self.api_key = api_key
        self.model = model

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    def complete(
        self,
        prompt: str,
        *,
        system: str = "",
        json_schema: dict | None = None,
        temperature: float = 0.0,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        if not self.configured:
            raise ProviderError(self.name, "no API key or model configured", retryable=False)

        max_tokens = max(max_tokens, MIN_MAX_TOKENS)  # leave room for reasoning
        body: dict = {
            "contents": [{"role": "user",
                          "parts": [{"text": prompt + _schema_instruction(json_schema)}]}],
            "generationConfig": {"temperature": temperature,
                                 "maxOutputTokens": max_tokens},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if json_schema:
            body["generationConfig"]["responseMimeType"] = "application/json"

        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent")
        try:
            r = httpx.post(url, headers={"x-goog-api-key": self.api_key},
                           json=body, timeout=TIMEOUT)
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"network error: {type(exc).__name__}") from exc

        if r.status_code != 200:
            raise ProviderError(self.name, f"HTTP {r.status_code}: {r.text[:180]}")

        try:
            data = r.json()
            candidate = data["candidates"][0]
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(self.name, f"unexpected response shape: {r.text[:180]}") from exc

        # Thinking models return their reasoning as parts flagged thought=true.
        # Join only the visible ones.
        parts = candidate.get("content", {}).get("parts", []) or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()

        if not text:
            finish = candidate.get("finishReason", "?")
            thoughts = (data.get("usageMetadata") or {}).get("thoughtsTokenCount", 0)
            raise ProviderError(
                self.name,
                f"empty content (finishReason={finish}, thoughtTokens={thoughts}) "
                f"- the reasoning consumed the whole budget; raise max_tokens",
            )
        return _strip_fences(text) if json_schema else text


class AnthropicCompatProvider:
    """A vendor speaking Anthropic's /v1/messages shape.

    Exists for Zhipu's GLM Coding Plan. The same GLM key reaches two different
    endpoints that are billed from two different pools:

        /api/paas/v4/chat/completions   pay-as-you-go, OpenAI-shaped
        /api/anthropic/v1/messages      the subscription, Anthropic-shaped

    Measured on this account: every paid model on the first returns
    `429 error 1113` -- insufficient balance -- while the second answers 200
    for glm-5.3 with the identical key. So this is not a nicer way to call the
    same thing; it is the only way to reach the plan that is actually paid for.
    """

    def __init__(self, *, name: str, base_url: str, api_key: str, model: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    def complete(
        self,
        prompt: str,
        *,
        system: str = "",
        json_schema: dict | None = None,
        temperature: float = 0.0,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        if not self.configured:
            raise ProviderError(self.name, "no API key or model configured", retryable=False)

        max_tokens = max(max_tokens, MIN_MAX_TOKENS)
        body: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user",
                          "content": prompt + _schema_instruction(json_schema)}],
        }
        # Anthropic's shape puts the system prompt beside the messages, not
        # inside them as a role.
        if system:
            body["system"] = system

        try:
            r = httpx.post(
                f"{self.base_url}/v1/messages",
                headers={"x-api-key": self.api_key,
                         "anthropic-version": ANTHROPIC_VERSION,
                         "Content-Type": "application/json"},
                json=body,
                timeout=SLOW_TIMEOUT,
            )
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"network error: {type(exc).__name__}") from exc

        if r.status_code != 200:
            raise ProviderError(self.name, f"HTTP {r.status_code}: {r.text[:180]}")

        try:
            blocks = r.json()["content"]
        except (KeyError, ValueError, TypeError) as exc:
            raise ProviderError(self.name, f"unexpected response shape: {r.text[:180]}") from exc

        # Thinking models emit `thinking` blocks alongside `text` ones. Join
        # only the visible text, the same way the Gemini provider does.
        text = "".join(
            b.get("text", "") for b in blocks
            if isinstance(b, dict) and b.get("type") == "text"
        ).strip()
        text = _strip_reasoning(text)
        if not text:
            raise ProviderError(
                self.name,
                "empty response after reasoning tokens - raise max_tokens",
            )
        return _strip_fences(text) if json_schema else text


# --- factories --------------------------------------------------------------

def glm() -> OpenAICompatProvider:
    return OpenAICompatProvider(
        name="glm",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=config.GLM_API_KEY,
        model=config.GLM_MODEL,
    )


def glm_coding() -> AnthropicCompatProvider:
    """GLM through the coding plan. Slow (17-23s measured) but genuinely paid
    for, which is why it sits at the very end of the chain rather than the
    front -- see providers/__init__.chain()."""
    return AnthropicCompatProvider(
        name="glm-coding",
        base_url=config.GLM_ANTHROPIC_BASE_URL,
        api_key=config.GLM_API_KEY,
        model=config.GLM_CODING_MODEL,
    )


def groq(model: str | None = None) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key=config.FALLBACK_API_KEY_GROQ,
        model=model or config.FALLBACK_MODEL_GROQ,
    )


def gemini() -> GeminiProvider:
    return GeminiProvider(
        api_key=config.FALLBACK_API_KEY_GEMINI,
        model=config.FALLBACK_MODEL_GEMINI,
    )
