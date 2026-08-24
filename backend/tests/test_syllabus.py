"""student-008 -- syllabus upload. No network, no database.

The interesting failures here are all *silent* ones: a scan that yields no text
and is read as "covers nothing", a model outage that certifies a student as
having no gaps, a mastery row invented from a syllabus line. Each is asserted
explicitly, because none of them raises anything on its own.
"""

from __future__ import annotations

import inspect
import json

import pytest

from app.providers.mock import MockProvider
from app.routers import student
from app.services import syllabus
from app.services.syllabus import Coverage, SyllabusError


SYLLABUS = (
    "Computer Science Workshop 1 — Syllabus\n"
    "Unit 1: Python programming. Data types, control flow, functions, "
    "object-oriented programming: classes, objects, inheritance and "
    "polymorphism. Packaging and dependency management.\n"
    "Unit 2: Web technologies. The client-server model, the request and "
    "response cycle, request methods, status codes, and URL structure.\n"
    "Unit 3: Introduction to databases. Tables, rows, primary keys, foreign "
    "keys and simple queries.\n"
)


# ---------------------------------------------------------------------------
# Reading the upload
# ---------------------------------------------------------------------------

def test_a_plain_text_syllabus_is_read():
    text = syllabus.extract_text("syllabus.txt", SYLLABUS.encode("utf-8"))
    assert "inheritance" in text
    assert "\n" not in text, "whitespace should be squashed to single spaces"


def test_a_file_with_no_extractable_text_is_rejected_not_treated_as_empty():
    """The failure this guards is silent: a scanned syllabus is a picture of
    text, PyMuPDF returns nothing, and 'covers no prerequisites' is then a
    maximal gap list built from zero evidence -- which looks like a result."""
    with pytest.raises(SyllabusError) as exc:
        syllabus.extract_text("scan.txt", b"Syllabus\n\n\n")
    assert exc.value.code == "no_text_found"


def test_an_empty_upload_is_rejected():
    with pytest.raises(SyllabusError) as exc:
        syllabus.extract_text("empty.pdf", b"")
    assert exc.value.code == "empty_file"


def test_an_oversized_upload_is_rejected_before_it_is_parsed():
    big = b"x" * (syllabus.MAX_UPLOAD_BYTES + 1)
    with pytest.raises(SyllabusError) as exc:
        syllabus.extract_text("huge.pdf", big)
    assert exc.value.code == "file_too_large"


def test_the_file_type_comes_from_the_bytes_not_the_extension():
    """Extension and browser-supplied content type are both caller-controlled.
    A PDF named .txt must still be parsed as a PDF."""
    source = inspect.getsource(syllabus.extract_text)
    assert "PDF_MAGIC" in source
    assert 'data[:5]' in source


def test_a_binary_upload_that_is_not_a_pdf_is_rejected_by_type():
    with pytest.raises(SyllabusError) as exc:
        syllabus.extract_text("notes.docx", b"PK\x03\x04" + b"\x00" * 400)
    assert exc.value.code == "unsupported_type"


def test_a_text_file_named_pdf_still_reads():
    """The extension is deliberately not consulted. Judging by the name made
    extract_text contradict its own promise: a syllabus saved as .pdf but
    really plain text is exactly the case byte-sniffing exists to handle, and
    it was being rejected as an unsupported type."""
    text = syllabus.extract_text("syllabus.pdf", SYLLABUS.encode("utf-8"))
    assert "inheritance" in text


def test_the_decode_path_never_looks_at_the_filename():
    body = inspect.getsource(syllabus._plain_text)
    body = body[body.rindex('"""') + 3:]
    assert "filename" not in body and "name." not in body


def test_a_very_long_syllabus_is_truncated_rather_than_sent_whole():
    text = syllabus.extract_text("long.txt", (SYLLABUS * 400).encode("utf-8"))
    assert len(text) == syllabus.MAX_SYLLABUS_CHARS


# ---------------------------------------------------------------------------
# Judging coverage -- the bias, and the failure modes
# ---------------------------------------------------------------------------

CONCEPTS = [
    {"slug": "class-inheritance", "name": "Class inheritance in Python",
     "topic": "Python foundations"},
    {"slug": "url-routing", "name": "URL paths and routing",
     "topic": "How the web works"},
]


def test_a_concept_missing_from_the_reply_counts_as_not_covered(monkeypatch):
    """Silence must not read as coverage. A model that forgets a concept would
    otherwise close a gap nobody ever looked at."""
    monkeypatch.setattr(
        syllabus, "complete",
        lambda *a, **k: type("R", (), {"text": json.dumps(
            {"concepts": [{"slug": "class-inheritance", "covered": True}]})})(),
    )
    out = {c.slug: c.covered for c in syllabus.assess(CONCEPTS, SYLLABUS)}
    assert out == {"class-inheritance": True, "url-routing": False}


def test_an_unparseable_reply_marks_everything_not_covered(monkeypatch):
    monkeypatch.setattr(
        syllabus, "complete",
        lambda *a, **k: type("R", (), {"text": "not json at all"})(),
    )
    assert all(not c.covered for c in syllabus.assess(CONCEPTS, SYLLABUS))


def test_a_slug_the_model_invented_is_ignored(monkeypatch):
    monkeypatch.setattr(
        syllabus, "complete",
        lambda *a, **k: type("R", (), {"text": json.dumps({"concepts": [
            {"slug": "quantum-teleportation", "covered": True},
            {"slug": "url-routing", "covered": True},
        ]})})(),
    )
    out = syllabus.assess(CONCEPTS, SYLLABUS)
    assert [c.slug for c in out] == ["class-inheritance", "url-routing"]
    assert [c.covered for c in out] == [False, True]


def test_one_model_call_for_the_whole_list_not_one_per_concept(monkeypatch):
    calls = []

    def fake(*a, **k):
        calls.append(1)
        return type("R", (), {"text": json.dumps({"concepts": []})})()

    monkeypatch.setattr(syllabus, "complete", fake)
    syllabus.assess(CONCEPTS, SYLLABUS)
    assert len(calls) == 1


def test_no_concepts_means_no_model_call_at_all(monkeypatch):
    monkeypatch.setattr(
        syllabus, "complete",
        lambda *a, **k: pytest.fail("assess() called the model with nothing to judge"),
    )
    assert syllabus.assess([], SYLLABUS) == []


def test_the_prompt_tells_the_model_to_resolve_doubt_toward_a_gap():
    """The bias is load-bearing and lives in prose, so it is asserted here --
    a well-meaning edit that softens it would otherwise pass every test."""
    from app import prompts

    text = prompts.load("syllabus_coverage").lower()
    assert "false" in text and "unclear" in text


# ---------------------------------------------------------------------------
# The mock provider must not fake a maximal gap list
# ---------------------------------------------------------------------------

def test_the_mock_provider_answers_the_coverage_shape(monkeypatch):
    """With the wifi off, the generic array fallback returns [], which the
    service reads as 'every prerequisite is a gap'. The mock has to do better
    than that or the offline demo shows a fake result."""
    monkeypatch.setattr(syllabus, "complete", lambda prompt, **k: type(
        "R", (), {"text": MockProvider().complete(
            prompt, json_schema=syllabus.COVERAGE_SCHEMA)})())
    out = {c.slug: c.covered for c in syllabus.assess(CONCEPTS, SYLLABUS)}
    assert out["class-inheritance"] is True, "the syllabus plainly teaches inheritance"
    assert out["url-routing"] is False, "and plainly does not teach Django routing"


# ---------------------------------------------------------------------------
# The route's guarantees
# ---------------------------------------------------------------------------

def test_the_upload_response_carries_no_score():
    source = inspect.getsource(student.syllabus_upload)
    body = source[source.index("return {"):]
    for banned in ("score", "percent", "grade", "correct_count", "total"):
        assert banned not in body.lower(), f"{banned!r} leaked into the upload response"


def test_both_entries_return_the_same_message_wording():
    """The frontend renders this string verbatim on the same screen, reached
    two ways. Two copies of the pluralisation is one copy too many."""
    for fn in (student.submit_diagnostic, student.syllabus_upload):
        assert "_gap_message(" in inspect.getsource(fn)
    assert student._gap_message(0) == "No prerequisite gaps found."
    assert student._gap_message(1) == "Found 1 prerequisite gap."
    assert student._gap_message(3) == "Found 3 prerequisite gaps."


def test_the_upload_writes_no_mastery_row():
    """A syllabus says a topic was taught, not that this student learned it.
    The diagnostic writes mastery because it has answers; this has none."""
    source = inspect.getsource(student.syllabus_upload)
    assert "Mastery" not in source


def test_gaps_from_an_upload_are_labelled_so_a_teacher_can_tell_them_apart():
    source = inspect.getsource(student.syllabus_upload)
    assert 'detected_from="syllabus_upload"' in source


def test_the_upload_only_ever_considers_prerequisite_concepts():
    """Current-course concepts are what this course is about to teach. Finding
    them absent from a prior syllabus is expected, and reporting them would
    bury the real gaps."""
    source = inspect.getsource(student.syllabus_upload)
    assert "Concept.prerequisite_course_id.is_not(None)" in source


def test_a_provider_outage_does_not_certify_the_student_as_gap_free():
    """The dangerous fallback is the quiet one: no model, no verdicts, no gaps,
    200 OK. The route must fail loudly instead."""
    source = inspect.getsource(student.syllabus_upload)
    assert "AllProvidersFailed" in source
    assert "HTTP_503_SERVICE_UNAVAILABLE" in source


def test_the_upload_requires_a_signed_in_user():
    params = inspect.signature(student.syllabus_upload).parameters
    assert "user" in params, "the route must depend on current_user"
