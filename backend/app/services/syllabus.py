"""student-008 -- turn an uploaded syllabus into the same gap list the
diagnostic produces.

The alternative entry for an incoming student. Instead of sitting eight
questions, they hand over the syllabus of what they have already studied, and
we work out which of the new course's prerequisites it never covered.

WHAT THIS DOES AND DOES NOT CLAIM
---------------------------------
A syllabus is evidence of *exposure*, not of *learning*. It says a topic was
taught, not that this student understood it. So a covered prerequisite produces
no gap and **no mastery row either** -- claiming "solid" because a topic
appeared on a syllabus would be inventing a measurement we never took. The
diagnostic writes mastery because it has answers; this has none.

THE BIAS RUNS OPPOSITE TO THE GUARDRAIL, ON PURPOSE
---------------------------------------------------
`guardrail.py` resolves uncertainty toward *answering*, because a wrong refusal
blocks a student who came to learn. Here uncertainty resolves toward *creating
the gap*, because the failures are not symmetric in the same direction:

  a false gap      -> a lesson the student does not need; they skip it, and
                      they can see it is wrong.
  a false coverage -> a real gap nobody ever finds. Silent, and it defeats the
                      entire point of the upload.

Visible over-detection beats invisible under-detection. See the same argument
spelled out for the model in `prompts/syllabus_coverage.md`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .. import prompts
from ..providers import complete

# A syllabus is a list of unit titles, not a book. Anything past this is either
# an appendix, a mark-distribution table, or the wrong document -- and sending
# it costs tokens and dilutes the part that matters.
MAX_SYLLABUS_CHARS = 12_000

# Below this there is nothing to judge. The overwhelmingly common cause is a
# scanned syllabus: a photograph of text inside a PDF wrapper, from which
# PyMuPDF extracts nothing. Treating that as "a syllabus covering no
# prerequisites" would hand the student a maximal gap list built from zero
# evidence, which is worse than refusing, because it looks like a real result.
MIN_SYLLABUS_CHARS = 200

# PyMuPDF opens what it is given. Cap before it does.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

PDF_MAGIC = b"%PDF-"

COVERAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "covered": {"type": "boolean"},
                    "evidence": {"type": "string"},
                },
                "required": ["slug", "covered"],
            },
        },
    },
    "required": ["concepts"],
}


class SyllabusError(ValueError):
    """The upload cannot be read. Carries the message shown to the student."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Coverage:
    """One prerequisite, judged. `evidence` is the syllabus phrase that
    convinced the model, so a student who disagrees with a gap can be shown
    why -- or shown that there was nothing."""

    slug: str
    covered: bool
    evidence: str = ""


# ---------------------------------------------------------------------------
# Reading the file
# ---------------------------------------------------------------------------

def extract_text(filename: str, data: bytes) -> str:
    """Plain text out of a PDF, .txt or .md upload.

    Sniffs the magic bytes rather than trusting the extension or the
    browser-supplied content type, both of which are attacker- and
    accident-controlled. A .txt that is really a PDF still parses; a .pdf that
    is really a text file still reads.
    """
    if not data:
        raise SyllabusError("empty_file", "That file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise SyllabusError(
            "file_too_large",
            f"That file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    if data[:5] == PDF_MAGIC:
        text = _pdf_text(data)
    else:
        text = _plain_text(filename, data)

    text = " ".join(text.split())
    if len(text) < MIN_SYLLABUS_CHARS:
        raise SyllabusError(
            "no_text_found",
            "I could not read any text from that file. If it is a scan or a "
            "photo of a syllabus, the text is an image -- please upload a "
            "text-based PDF, or paste the syllabus into a .txt file.",
        )
    return text[:MAX_SYLLABUS_CHARS]


def _pdf_text(data: bytes) -> str:
    import pymupdf   # `fitz` is the deprecated spelling of the same module

    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:                      # noqa: BLE001 - vendor error
        raise SyllabusError("unreadable_pdf", f"That PDF could not be opened: {exc}")
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


# latin-1 maps every possible byte to some character, so "it decoded" proves
# nothing about whether the bytes were ever text. A .docx is a zip and decodes
# into control-character noise. This is the line between the two.
MIN_PRINTABLE_RATIO = 0.85


def _plain_text(filename: str, data: bytes) -> str:
    """Decode a non-PDF upload, judging it by its content rather than its name.

    The extension is deliberately not consulted. It was, once, and it made this
    function contradict the promise in `extract_text` -- a syllabus saved as
    `.pdf` but really plain text was rejected as an unsupported type, which is
    exactly the case the byte sniffing exists to handle. What actually needs
    rejecting is a binary format like .docx, and that is a property of the
    bytes, not of the four characters after the dot.
    """
    text = None
    for encoding in ("utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise SyllabusError("unsupported_type", "That file is not readable as text.")

    printable = sum(1 for ch in text if ch.isprintable() or ch.isspace())
    if not text or printable / len(text) < MIN_PRINTABLE_RATIO:
        raise SyllabusError(
            "unsupported_type",
            "That file does not look like text. Please upload the syllabus as "
            "a PDF, .txt or .md file -- Word documents are not supported.",
        )
    return text


# ---------------------------------------------------------------------------
# Judging it
# ---------------------------------------------------------------------------

def assess(concepts: list[dict], syllabus_text: str) -> list[Coverage]:
    """One model call for the whole list, not one per concept.

    Batching is not only cheaper. The model sees the syllabus once and decides
    against the whole prerequisite set at once, so "Unit 3 covers inheritance
    but nothing about virtual environments" is a single coherent judgement
    rather than eight independent ones that can contradict each other.

    `concepts` is `[{"slug": ..., "name": ..., "topic": ...}, ...]`.

    A concept missing from the reply, or a reply that will not parse at all,
    counts as NOT covered -- the same direction the prompt's bias runs. A model
    failure must not silently certify a student as having no gaps.
    """
    if not concepts:
        return []

    listing = "\n".join(
        f"- `{c['slug']}` -- {c['name']}"
        + (f" (topic: {c['topic']})" if c.get("topic") else "")
        for c in concepts
    )
    result = complete(
        prompts.render("syllabus_coverage", concepts=listing, syllabus=syllabus_text),
        json_schema=COVERAGE_SCHEMA,
        max_tokens=2048,
    )

    verdicts: dict[str, Coverage] = {}
    try:
        parsed = json.loads(result.text)
        rows = parsed["concepts"]
        if not isinstance(rows, list):
            raise TypeError("concepts was not a list")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        rows = []

    known = {c["slug"] for c in concepts}
    for row in rows:
        if not isinstance(row, dict):
            continue
        slug = str(row.get("slug", "")).strip()
        if slug not in known:
            continue
        verdicts[slug] = Coverage(
            slug=slug,
            covered=bool(row.get("covered", False)),
            evidence=str(row.get("evidence", ""))[:300],
        )

    return [
        verdicts.get(c["slug"], Coverage(slug=c["slug"], covered=False))
        for c in concepts
    ]
