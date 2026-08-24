"""ingest-001 tests. No network, no database.

The fixture builds a real PDF with PyMuPDF and then reads it back, so the text
under test has genuinely been through a PDF text layer -- soft-wrapped, split
across pages, hyphenated at line ends. Asserting against a hand-written string
would test nothing, because the bugs this pipeline can have all live in that
round trip.

What matters here is the invariant the citation story rests on: a chunk is a
slice of exactly one page. Everything else is detail.
"""

from __future__ import annotations

import pytest

from app.services import ingest

pymupdf = pytest.importorskip("pymupdf")


PAGE_1 = (
    "Newton's first law states that a body continues in its state of rest, or of "
    "uniform motion in a straight line, unless acted upon by a net external force. "
    "The key consequence is that motion itself does not require a force. A force is "
    "required only to change motion. A body moving at constant velocity therefore "
    "has zero net force acting on it, no matter how fast it is moving. This is the "
    "single most common source of confusion in introductory mechanics, and it is "
    "worth stating twice: constant velocity means zero net force. "
    "Newton's second law relates the net force on a body to its acceleration, "
    "written F_net = m a, where the net force is the vector sum of every force "
    "acting on the body. If a net force of twelve newtons acts on a mass of four "
    "kilograms, the acceleration is three metres per second squared, directed "
    "along the net force. Newton's third law states that if body A exerts a force "
    "on body B, then body B exerts an equal and opposite force on body A. The two "
    "forces of a third-law pair always act on different bodies, which is why the "
    "weight of a book and the normal force from the table beneath it are not a "
    "third-law pair: both of those act on the book, and they happen to be equal "
    "only because the book is in equilibrium."
)

PAGE_2 = (
    "When a block slides across a rough floor at constant speed, the applied push "
    "and the force of kinetic friction are equal in magnitude and opposite in "
    "direction. Their vector sum is zero, so the net force is zero and the "
    "acceleration is zero. Constant velocity and zero net force always accompany "
    "one another. Resolving a force into perpendicular components is the standard "
    "technique for handling an inclined plane."
)

PAGE_3 = "Figure 5.1"          # too short to be worth a chunk


@pytest.fixture(scope="module")
def pdf_path(tmp_path_factory):
    """A three-page PDF with an outline, written by PyMuPDF and read back."""
    path = tmp_path_factory.mktemp("ingest") / "mechanics.pdf"
    doc = pymupdf.open()
    for body in (PAGE_1, PAGE_2, PAGE_3):
        page = doc.new_page()
        # A narrow box forces soft wrapping and end-of-line hyphenation, which
        # is exactly the mess normalise() has to undo.
        page.insert_textbox(pymupdf.Rect(60, 60, 320, 700), body, fontsize=11)
    doc.set_toc([[1, "5. Newton's Laws of Motion", 1], [1, "6. Friction", 2]])
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture(scope="module")
def parsed(pdf_path):
    return ingest.parse_pdf(pdf_path)


# --- normalisation ----------------------------------------------------------

def test_soft_wraps_become_spaces_paragraph_breaks_survive():
    out = ingest.normalise("a net external\nforce acts\n\non the body")
    assert out == "a net external force acts\n\non the body"


def test_hyphen_split_across_a_line_break_is_rejoined():
    assert ingest.normalise("accelera-\ntion is zero") == "acceleration is zero"


def test_a_real_hyphenated_compound_is_left_alone():
    # No line break, so nothing to repair -- "free-body" must stay hyphenated.
    assert ingest.normalise("a free-body diagram") == "a free-body diagram"


def test_normalise_is_idempotent():
    """verify_material() re-runs it long after ingestion; a second pass that
    changed the text would fail every audit."""
    once = ingest.normalise("accelera-\ntion\nis  zero\n\nnext para")
    assert ingest.normalise(once) == once


# --- chunking ---------------------------------------------------------------

def test_chunks_are_slices_and_cover_the_text_in_order():
    text = ingest.normalise(PAGE_1)
    spans = ingest.chunk_spans(text)
    assert spans
    assert spans[0][0] == 0
    assert spans[-1][1] == len(text)
    for start, end in spans:
        assert 0 <= start < end <= len(text)
    assert [s for s, _ in spans] == sorted(s for s, _ in spans)


def test_consecutive_chunks_overlap_rather_than_abut():
    """One sentence of overlap, so a definition at a chunk edge is still
    retrievable with the sentence that uses it."""
    long_text = ingest.normalise(" ".join([PAGE_1, PAGE_2] * 2))
    spans = ingest.chunk_spans(long_text)
    assert len(spans) > 1
    assert any(spans[i + 1][0] < spans[i][1] for i in range(len(spans) - 1))


def test_a_page_with_no_punctuation_is_hard_split_not_dropped():
    text = "word " * 900                     # far past MAX_CHARS, zero sentences
    spans = ingest.chunk_spans(ingest.normalise(text))
    assert len(spans) > 1
    assert all(end - start <= ingest.MAX_CHARS for start, end in spans)


def test_no_stub_tail_chunk():
    text = ingest.normalise(PAGE_1 + " " + PAGE_2)
    spans = ingest.chunk_spans(text)
    assert all(end - start >= ingest.MIN_CHUNK_CHARS for start, end in spans)


def test_empty_text_yields_no_chunks():
    assert ingest.chunk_spans("") == []


# --- the invariant ----------------------------------------------------------

def test_every_chunk_is_an_exact_slice_of_its_own_page(pdf_path, parsed):
    """The load-bearing assertion of ingest-001.

    If this passes, a citation's page number cannot be wrong: the text was cut
    out of that page and never rebuilt.
    """
    pages = {c.page_no for c in parsed.chunks}
    page_text = {n: ingest.page_text(pdf_path, n) for n in pages}
    for c in parsed.chunks:
        assert page_text[c.page_no][c.char_start:c.char_end] == c.text

    # Non-vacuous: if every span started at 0 the assertion above would hold
    # even with char_start hard-coded wrong.
    assert any(c.char_start > 0 for c in parsed.chunks)


def test_chunk_text_appears_on_its_page_independently_of_the_span(pdf_path, parsed):
    """Second, independent check: ignore our offsets entirely and look for the
    text in a fresh extraction. A wrong char_start cannot pass both."""
    doc = pymupdf.open(str(pdf_path))
    try:
        raw = {n: doc[n - 1].get_text("text") for n in {c.page_no for c in parsed.chunks}}
    finally:
        doc.close()
    for c in parsed.chunks:
        assert ingest.squash(c.text) in ingest.squash(raw[c.page_no])


def test_no_chunk_leaks_text_from_a_neighbouring_page(pdf_path, parsed):
    """A chunk spanning a page break could not honestly claim either page."""
    page_two_only = "inclined plane"
    for c in parsed.chunks:
        if page_two_only in c.text:
            assert c.page_no == 2


def test_page_numbers_are_one_based_and_real(parsed):
    assert min(c.page_no for c in parsed.chunks) == 1
    assert max(c.page_no for c in parsed.chunks) <= parsed.page_count


def test_every_chunk_has_the_three_fields_citations_need(parsed):
    for c in parsed.chunks:
        assert c.page_no >= 1
        assert c.char_end > c.char_start
        assert c.text.strip()


# --- pages and chapters -----------------------------------------------------

def test_a_page_with_almost_no_text_produces_no_chunks(parsed):
    assert parsed.page_count == 3
    assert parsed.pages_with_text == 2
    assert all(c.page_no != 3 for c in parsed.chunks)


def test_chapter_comes_from_the_pdf_outline(parsed):
    by_page = {c.page_no: c.chapter for c in parsed.chunks}
    assert by_page[1] == "5. Newton's Laws of Motion"
    assert by_page[2] == "6. Friction"


def test_chapter_is_none_when_the_book_has_no_outline(tmp_path):
    """A guessed chapter heading is worse than an absent one -- it renders on a
    citation as if it were fact."""
    path = tmp_path / "no-outline.pdf"
    doc = pymupdf.open()
    doc.new_page().insert_textbox(pymupdf.Rect(60, 60, 320, 700), PAGE_1, fontsize=11)
    doc.save(str(path))
    doc.close()

    assert all(c.chapter is None for c in ingest.parse_pdf(path).chunks)


def test_chapter_for_page_picks_the_last_chapter_that_started():
    index = [(1, "One"), (10, "Two"), (25, "Three")]
    assert ingest.chapter_for_page(index, 1) == "One"
    assert ingest.chapter_for_page(index, 9) == "One"
    assert ingest.chapter_for_page(index, 10) == "Two"
    assert ingest.chapter_for_page(index, 99) == "Three"
    assert ingest.chapter_for_page([], 5) is None


# --- guards -----------------------------------------------------------------

def test_ingest_material_rejects_an_unknown_kind(tmp_path):
    """kind drives the guardrail: an assignment ingested as a textbook would be
    served to a student as course material."""
    with pytest.raises(ValueError, match="kind must be one of"):
        ingest.ingest_material(None, course_id=1, title="x", kind="homework",
                               path=tmp_path / "nope.pdf")
