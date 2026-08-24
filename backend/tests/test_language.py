"""i18n-001 tests. No network, no database.

The pipeline is: translate in -> retrieve in English -> answer in English ->
translate out. Everything worth testing here is about where those two edges
sit, because the alignment score and the citations are only stable across
languages if nothing between the edges ever sees a non-English string.
"""

from __future__ import annotations

import inspect

import pytest

from app.services import language as lang


# ---------------------------------------------------------------------------
# Language codes
# ---------------------------------------------------------------------------

def test_an_unknown_language_falls_back_rather_than_raising():
    """A student whose profile carries a language we cannot translate should
    get an English answer, not an error page. The answer is the point."""
    assert lang.normalise("zz") == "en"
    assert lang.normalise("") == "en"
    assert lang.normalise(None) == "en"
    assert lang.normalise("HI") == "hi"
    assert lang.normalise("hi-IN") == "hi"


def test_every_offered_language_is_one_the_pipeline_accepts():
    from app import config

    for entry in config.LANGUAGES:
        assert lang.normalise(entry["code"]) == entry["code"]


# ---------------------------------------------------------------------------
# Chunking -- Sarvam's length ceiling
# ---------------------------------------------------------------------------

def test_long_text_is_split_below_the_api_ceiling():
    """A gap lesson runs to two or three thousand characters and the endpoint
    takes about a thousand. translate() returns its input unchanged on
    failure, so an over-length call looks exactly like 'already English'."""
    text = "\n\n".join("This is a sentence about Django models. " * 30
                       for _ in range(4))
    chunks = lang.split_for_translation(text)
    assert len(chunks) > 1
    assert all(len(c) <= lang.MAX_CHUNK_CHARS for c in chunks)


def test_short_text_is_not_split():
    assert lang.split_for_translation("Hello.") == ["Hello."]
    assert lang.split_for_translation("") == []


def test_a_single_oversized_sentence_is_cut_rather_than_dropped():
    chunks = lang.split_for_translation("x" * (lang.MAX_CHUNK_CHARS * 2 + 50))
    assert all(len(c) <= lang.MAX_CHUNK_CHARS for c in chunks)
    assert sum(len(c) for c in chunks) == lang.MAX_CHUNK_CHARS * 2 + 50


def test_splitting_prefers_sentence_boundaries():
    """A clause cut in half mid-way translates into nonsense that reads as a
    model failure."""
    text = ("A QuerySet is lazy. " * 60)
    for chunk in lang.split_for_translation(text):
        assert not chunk.endswith("QuerySet is")


# ---------------------------------------------------------------------------
# The honesty of the reported language
# ---------------------------------------------------------------------------

def test_translation_that_did_not_happen_is_reported_as_english(monkeypatch):
    monkeypatch.setattr(lang, "available", lambda: True)
    monkeypatch.setattr(lang.translate_sarvam, "translate", lambda text, **kw: text)
    body, produced = lang.from_english("A QuerySet is lazy.", "hi")
    assert produced == "en", "an unchanged translation is not a translation"
    assert body == "A QuerySet is lazy."


def test_no_api_key_means_english_is_reported(monkeypatch):
    monkeypatch.setattr(lang, "available", lambda: False)
    _, produced = lang.from_english("A QuerySet is lazy.", "hi")
    assert produced == "en"


def test_a_real_translation_is_reported_as_the_target(monkeypatch):
    monkeypatch.setattr(lang, "available", lambda: True)
    monkeypatch.setattr(lang.translate_sarvam, "translate",
                        lambda text, **kw: f"[{kw['to']}] {text}")
    body, produced = lang.from_english("A QuerySet is lazy.", "hi")
    assert produced == "hi"
    assert body.startswith("[hi] ")


def test_english_out_is_never_sent_to_the_translator(monkeypatch):
    monkeypatch.setattr(lang, "available", lambda: True)
    monkeypatch.setattr(lang.translate_sarvam, "translate",
                        lambda *a, **k: pytest.fail("translated en -> en"))
    assert lang.from_english("A QuerySet is lazy.", "en") == ("A QuerySet is lazy.", "en")


# ---------------------------------------------------------------------------
# The inbound edge -- the bug that moved the alignment score
# ---------------------------------------------------------------------------

def test_the_inbound_translation_auto_detects_rather_than_trusting_the_request(
        monkeypatch):
    """`language` means "the language I want to read in". A student who picks
    Hindi in the UI and types an English question is ordinary, not an error.

    Declaring the source as Hindi for English text is NOT a no-op: Sarvam
    rewords it, the reworded text is what gets embedded, and it retrieves
    different passages. Measured live: the same English question scored 88%
    with language=en and 82% with language=hi, with different citations.
    """
    seen = {}

    def fake(text, **kw):
        seen.update(kw)
        return "translated"

    monkeypatch.setattr(lang, "available", lambda: True)
    monkeypatch.setattr(lang.translate_sarvam, "translate", fake)
    lang.to_english("कुछ", "hi")

    assert seen.get("source") == "auto", (
        "the declared request language must not be used as the translation source"
    )
    assert seen.get("to") == "en"


def test_an_english_question_is_not_translated_inbound(monkeypatch):
    monkeypatch.setattr(lang, "available", lambda: True)
    monkeypatch.setattr(lang.translate_sarvam, "translate",
                        lambda *a, **k: pytest.fail("translated an English question"))
    assert lang.to_english("what is a QuerySet?", "en") == "what is a QuerySet?"


# ---------------------------------------------------------------------------
# Where the edges sit, asserted against the pipeline itself
# ---------------------------------------------------------------------------

def test_the_evidence_check_runs_on_english_not_on_the_students_text():
    """If assess() ever saw the raw question, the alignment badge would drift
    between languages and the citation numbers with it."""
    from app.services import tutor

    source = inspect.getsource(tutor.ask)
    assert "evidence.assess(asked_in_english" in source
    assert "retrieval.search(db, asked_in_english" in source
    assert "guardrail.check(db, asked_in_english" in source


def test_the_answer_is_translated_after_the_evidence_check(monkeypatch):
    from app.services import tutor

    source = inspect.getsource(tutor.ask)
    assert source.index("evidence.assess(") < source.index("lang.from_english(result.text")


def test_citations_and_evidence_are_never_translated():
    from app.services import tutor

    for fn in (tutor.ask, tutor.lesson):
        source = inspect.getsource(fn)
        assert "from_english(cites" not in source
        assert "from_english(report" not in source


def test_an_uncertainty_flag_stores_the_english_question():
    """A teacher reading the panel should not need the student's language to
    know what was asked, and the panel is one list mixing every language."""
    from app.services import tutor

    source = inspect.getsource(tutor.ask)
    assert "question=asked_in_english[:2000]" in source
