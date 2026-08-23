"""Sarvam translation, behind the same cache as model calls.

Pipeline: translate in -> retrieve in English -> answer in English -> translate
out. The vector space stays English-only, which is why we do not need a
multilingual embedding model.

Citations always keep pointing at the English source book and page, and the
alignment score is computed on the English text - so the score is identical
whether the student asked in English or Hindi. That is a real property worth
stating in the pitch, not a side effect.
"""

from __future__ import annotations

import httpx

from .. import config
from . import cache
from .base import ProviderError

ENDPOINT = "https://api.sarvam.ai/translate"
TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)

# Sarvam expects BCP-47-ish codes.
_LANG = {
    "en": "en-IN", "hi": "hi-IN", "bn": "bn-IN", "ta": "ta-IN",
    "te": "te-IN", "mr": "mr-IN", "gu": "gu-IN", "kn": "kn-IN",
    "ml": "ml-IN", "pa": "pa-IN", "or": "od-IN",
}


def _code(lang: str) -> str:
    return _LANG.get(lang.lower(), f"{lang.lower()}-IN")


def translate(text: str, *, to: str, source: str = "auto") -> str:
    """Translate text. Returns the input unchanged when translation is a no-op
    or unavailable -- a failed translation must never break a lesson.
    """
    if not text or not text.strip():
        return text
    if to == source or (to == "en" and source == "en"):
        return text

    key = cache.make_key(text, system=f"translate:{source}->{to}")
    hit = cache.get(key)
    if hit is not None:
        return hit["text"]

    if not config.SARVAM_API_KEY:
        return text

    try:
        r = httpx.post(
            ENDPOINT,
            headers={"api-subscription-key": config.SARVAM_API_KEY,
                     "Content-Type": "application/json"},
            json={
                "input": text,
                "source_language_code": "auto" if source == "auto" else _code(source),
                "target_language_code": _code(to),
                "speaker_gender": "Female",
                "mode": "formal",
                "enable_preprocessing": True,
            },
            timeout=TIMEOUT,
        )
    except httpx.HTTPError:
        return text

    if r.status_code != 200:
        return text

    try:
        out = r.json().get("translated_text") or text
    except ValueError:
        return text

    cache.put(key, text=out, provider="sarvam", model="mayuri")
    return out


def translate_strict(text: str, *, to: str, source: str = "auto") -> str:
    """Same, but raises instead of silently passing text through. Use where a
    silent no-op would be misleading, e.g. a translation self-test."""
    if not config.SARVAM_API_KEY:
        raise ProviderError("sarvam", "SARVAM_API_KEY is not set", retryable=False)
    out = translate(text, to=to, source=source)
    if out == text and to != source:
        raise ProviderError("sarvam", "translation returned the input unchanged")
    return out
