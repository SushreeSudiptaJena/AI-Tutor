"""i18n-001 -- the translation edges of the pipeline.

    question (any language) -> English -> retrieve -> answer in English
                                                   -> back to the student's language

The vector space is English only, which is the whole reason a multilingual
embedding model is not needed. Two consequences are worth stating rather than
discovering:

* **Citations always name the English source book and page.** They are produced
  by retrieval, which never sees the student's language. A Hindi answer cites
  page 83 of the same book the English answer cites.
* **The alignment score is computed on English text**, before any translation
  out. So the badge does not drift between languages: the same question asked
  in Hindi and in English scores identically. That is a property of where the
  translation boundary sits, not a coincidence.

WHY THE CHUNKING EXISTS
-----------------------
Sarvam's translate endpoint takes roughly a thousand characters per call. A gap
lesson runs to two or three thousand. Sending the whole body means the tail is
silently dropped or the request is rejected -- and `translate()` returns the
input unchanged on failure, so a rejected call looks exactly like "this text
was already English". The student would get a half-translated lesson, or an
English one, with nothing anywhere saying why.

So text is split on paragraph and then sentence boundaries before it goes out,
and reassembled after. Splitting on sentences rather than at a character count
matters: a clause cut in half mid-way translates into nonsense that reads as a
model failure.
"""

from __future__ import annotations

import re

from .. import config
from ..providers import translate_sarvam

# Sarvam's documented ceiling is 1000 characters. Leave room rather than sit on
# the boundary: the count that matters is the API's, not Python's, and they can
# disagree about what a character is once the text is not ASCII.
MAX_CHUNK_CHARS = 800

SUPPORTED = {lang["code"] for lang in config.LANGUAGES}

_SENTENCE_END = re.compile(r"(?<=[.!?।])\s+")
_LANG_CODE = re.compile(r"^[a-z]{2}$")


def normalise(language: str | None, *, fallback: str = "en") -> str:
    """A two-letter code we are willing to act on, or the fallback.

    An unknown code resolves to the fallback rather than raising. A student
    whose profile carries a language we cannot translate should get an English
    answer, not an error page -- the answer is the point.
    """
    if not language:
        return fallback
    code = language.strip().lower()[:2]
    if not _LANG_CODE.match(code):
        return fallback
    return code if code in SUPPORTED else fallback


def is_english(language: str | None) -> bool:
    return normalise(language) == "en"


def available() -> bool:
    """Whether translation can actually happen. Without a key every call is a
    silent pass-through, and reporting `language: "hi"` over English text would
    be a claim we did not earn."""
    return bool(config.SARVAM_API_KEY)


def split_for_translation(text: str, limit: int = MAX_CHUNK_CHARS) -> list[str]:
    """Paragraphs first, then sentences, then a hard cut as a last resort.

    The hard cut is reachable only for a single sentence longer than the limit,
    which in practice means a code block or a run-on. It is better than
    dropping the text.
    """
    if len(text) <= limit:
        return [text] if text else []

    chunks: list[str] = []
    for paragraph in text.split("\n\n"):
        if not paragraph.strip():
            continue
        if len(paragraph) <= limit:
            chunks.append(paragraph)
            continue

        current = ""
        for sentence in _SENTENCE_END.split(paragraph):
            if len(sentence) > limit:
                if current:
                    chunks.append(current)
                    current = ""
                for i in range(0, len(sentence), limit):
                    chunks.append(sentence[i:i + limit])
                continue
            if len(current) + len(sentence) + 1 > limit:
                chunks.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            chunks.append(current)
    return chunks


def to_english(text: str, source: str) -> str:
    """Inbound: the student's question, into the language the corpus is in.

    `source` selects whether to translate at all; the actual translation is
    always done with **auto-detection**, never with `source` as the declared
    language. Those are different questions. `language` on the request means
    "the language I want to read in", and a student who picks Hindi in the UI
    and then types an English question is ordinary, not an error.

    Declaring the source as Hindi for English text is not a no-op: Sarvam
    dutifully "translates" it and returns a reworded sentence. That reworded
    text is what gets embedded, so it retrieves slightly different passages --
    the same English question scored 88% with `language=en` and 82% with
    `language=hi`, with different citations. Auto-detection removes the whole
    class of problem.
    """
    if is_english(normalise(source)) or not text.strip() or not available():
        return text
    return " ".join(
        translate_sarvam.translate(chunk, to="en", source="auto")
        for chunk in split_for_translation(text)
    ).strip()


def from_english(text: str, target: str) -> tuple[str, str]:
    """Outbound. Returns `(text, language_actually_produced)`.

    The second value is the honest part. `translate()` returns its input
    unchanged when the call fails, so a caller that assumed success would label
    English prose as Hindi and the student would be told the system had
    answered in their language when it had not. Reporting `en` on a failed
    translation is worse-looking and correct.
    """
    target = normalise(target)
    if is_english(target) or not text.strip():
        return text, "en"
    if not available():
        return text, "en"

    chunks = split_for_translation(text)
    translated = [
        translate_sarvam.translate(chunk, to=target, source="en")
        for chunk in chunks
    ]

    # If nothing came back changed, the call did not happen. One unchanged
    # chunk is ordinary -- a heading, a formula, a line that is the same in
    # both languages -- so the test is whether ANY chunk moved.
    if not any(new != old for new, old in zip(translated, chunks)):
        return text, "en"

    joined = "\n\n".join(translated) if len(chunks) > 1 else translated[0]
    return joined, target
