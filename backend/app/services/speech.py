"""a11y-001, the backend half -- text that survives being read aloud.

`TutorResponse.body` is markdown, because it renders as a lesson card. The
contract points read-aloud at that same field, and markdown read aloud is not
the same document:

* `[4]` is a citation marker on screen. `speechSynthesis` says **"four"**, in
  the middle of a sentence, and the student hears "...returns model instances
  when executed four."  That is not a formatting blemish; it is a wrong
  sentence.
* `**lazy**` and `` `Post.objects.all()` `` are emphasis and code on screen.
  Aloud they are either silence with an odd pause or a run of punctuation
  names, depending on the engine and the platform.
* `#` headings and `-` bullets read as "hash" and "dash" on some engines and
  vanish on others, so the structure a sighted student sees is either noise or
  nothing.

So the server sends a second rendering of the same answer, `speech_text`,
alongside the markdown one. Doing it here rather than in the browser is
deliberate: there is one implementation instead of one per page, and the
frontend pages are owned by three different people.

WHAT THIS IS NOT
----------------
Not a markdown parser. It is a small, total function over the narrow subset of
markdown these prompts actually produce, and its failure mode is leaving a
stray character in speech rather than throwing. A dependency to strip six
constructs would be a poor trade at this size.
"""

from __future__ import annotations

import re

# Order matters: citation markers go before punctuation cleanup, or the digits
# survive as bare numbers, which is the exact failure this exists to prevent.
_CITATION = re.compile(r"\s*\[\s*\d+(?:\s*,\s*\d+)*\s*\]")
_FENCE = re.compile(r"```[\w-]*\n(.*?)```", re.DOTALL)
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD_ITALIC = re.compile(r"(\*{1,3}|_{1,3})(\S(?:.*?\S)?)\1", re.DOTALL)
_HEADING = re.compile(r"(?m)^\s{0,3}#{1,6}\s*")
_BULLET = re.compile(r"(?m)^\s{0,3}[-*+]\s+")
_NUMBERED = re.compile(r"(?m)^\s{0,3}(\d+)[.)]\s+")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_BLOCKQUOTE = re.compile(r"(?m)^\s{0,3}>\s?")
_RULE = re.compile(r"(?m)^\s{0,3}([-*_]\s*){3,}$")
_MULTISPACE = re.compile(r"[ \t]{2,}")
_MULTINEWLINE = re.compile(r"\n{3,}")


def for_speech(markdown: str) -> str:
    """A plain-text rendering of `markdown` suitable for `speechSynthesis`.

    Citation markers are removed rather than spoken. A student listening cannot
    act on "[4]" anyway -- they cannot click it -- and the citation list is
    still on screen and still in `citations[]` for anyone who wants it. Reading
    the number aloud is strictly worse than silence.
    """
    if not markdown or not markdown.strip():
        return ""

    text = markdown

    # Links before anything else, so the visible label survives and the URL
    # does not get read out one slash at a time.
    text = _LINK.sub(r"\1", text)

    # Code fences keep their contents. A lesson's example is often the point of
    # the paragraph before it, and dropping it would remove the answer.
    text = _FENCE.sub(lambda m: m.group(1), text)
    text = _INLINE_CODE.sub(r"\1", text)

    text = _CITATION.sub("", text)
    text = _RULE.sub("", text)
    text = _HEADING.sub("", text)
    text = _BLOCKQUOTE.sub("", text)

    # A bullet becomes a sentence break. Without the full stop the engine runs
    # consecutive list items together into one long clause.
    text = _BULLET.sub("", text)
    text = _NUMBERED.sub(r"\1. ", text)

    # Emphasis last: earlier passes can expose markers that were inside code.
    for _ in range(2):
        text = _BOLD_ITALIC.sub(r"\2", text)

    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = _MULTISPACE.sub(" ", text)
    text = _MULTINEWLINE.sub("\n\n", text)

    lines = [ln.rstrip() for ln in text.split("\n")]
    return "\n".join(lines).strip()
