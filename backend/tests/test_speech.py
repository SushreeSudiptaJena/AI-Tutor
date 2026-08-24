"""a11y-001, the backend half. No network, no database.

`TutorResponse.body` is markdown because it renders as a lesson card, and the
contract points read-aloud at that same field. Markdown read aloud is not the
same document, and the citation markers are the worst of it: `[4]` is spoken
as "four", mid-sentence.
"""

from __future__ import annotations

import inspect

from app.services import speech, tutor


def test_citation_markers_are_removed_not_spoken():
    """The failure this exists to prevent: '...when executed four.'

    A listening student cannot click a citation anyway, and the list is still
    on screen and still in `citations[]`. Silence beats a stray number.
    """
    out = speech.for_speech("It runs when evaluated [4]. Chain filters [2, 3].")
    assert "4" not in out and "[" not in out
    assert out == "It runs when evaluated. Chain filters."


def test_emphasis_markers_do_not_survive():
    assert speech.for_speech("QuerySets are **lazy** and _useful_.") == \
        "QuerySets are lazy and useful."


def test_inline_code_keeps_its_contents():
    """The example is often the point of the sentence around it."""
    assert speech.for_speech("Call `Post.objects.all()` first.") == \
        "Call Post.objects.all() first."


def test_a_fenced_code_block_is_kept_not_dropped():
    out = speech.for_speech("Do this:\n\n```python\nx = 1\n```\n")
    assert "x = 1" in out
    assert "```" not in out and "python" not in out


def test_headings_and_bullets_lose_their_markers():
    out = speech.for_speech("## Title\n\n- one\n- two\n")
    assert "#" not in out and out.count("-") == 0
    assert "Title" in out and "one" in out and "two" in out


def test_a_numbered_list_keeps_its_numbers():
    """Unlike a citation, an ordinal is part of the sentence: 'one, build the
    query' is what the student needs to hear."""
    out = speech.for_speech("1. Build it.\n2. Run it.\n")
    assert "1." in out and "2." in out


def test_a_link_is_spoken_as_its_label_not_its_url():
    out = speech.for_speech("See [the docs](https://example.com/a/b) for more.")
    assert "the docs" in out
    assert "example.com" not in out and "https" not in out


def test_smart_quotes_are_normalised():
    assert '"' in speech.for_speech('A “recipe” for rows.')


def test_empty_input_is_empty_output_not_an_error():
    assert speech.for_speech("") == ""
    assert speech.for_speech("   \n\n ") == ""


def test_plain_prose_is_returned_unchanged():
    text = "A QuerySet is lazy. It runs when you iterate it."
    assert speech.for_speech(text) == text


def test_it_never_raises_on_malformed_markdown():
    """Its failure mode is a stray character in speech, never an exception --
    a lesson must not 500 because a model emitted an unbalanced asterisk."""
    for bad in ("**unclosed", "`unclosed", "[4", "](", "```\nx", "*" * 40,
                "###", "> ", "[]()", "_"):
        assert isinstance(speech.for_speech(bad), str)


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------

def test_every_answer_path_ships_a_speech_rendering():
    """Including the refusals. A student who cannot see the screen still needs
    to hear why they were refused."""
    for fn in (tutor.ask, tutor.lesson):
        source = inspect.getsource(fn)
        returns = source.count('"outcome"')
        assert source.count('"speech_text"') == returns, (
            f"{fn.__name__} has {returns} outcomes but "
            f"{source.count('\"speech_text\"')} speech renderings"
        )


def test_speech_text_is_built_from_the_translated_body():
    """It must be spoken in the language the student is reading, so it is
    derived from `body` after translation, not from the English source."""
    for fn in (tutor.ask, tutor.lesson):
        source = inspect.getsource(fn)
        assert "speech.for_speech(body)" in source
        assert "speech.for_speech(result.text" not in source
