"""concept-001 tests -- concepts read out of the corpus. No network, no database.

Two things are being protected here, and they pull in opposite directions.

The first is that a derived syllabus is allowed to be large: that is the point,
and every endpoint that enumerates concepts has to survive it. The second is
that making it large must not quietly break the things that were true when it
was fifteen rows -- the golden path's eight diagnostic questions, the
no-aggregate-score stance on mastery, and the fact that `seed.py` deletes
anything the seed files do not define.
"""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

import pytest

from app.routers import admin, student


def _src(fn) -> str:
    return inspect.getsource(fn)


@pytest.fixture(scope="module")
def derive():
    """Import the derivation script by path -- it lives in scripts/, not app/."""
    path = Path(__file__).resolve().parents[1] / "scripts" / "derive_concepts.py"
    spec = importlib.util.spec_from_file_location("derive_concepts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Chunk:
    """Only `.chapter` is read by windows()."""

    def __init__(self, chapter):
        self.chapter = chapter


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

def test_a_concept_records_where_it_came_from():
    from app.models import Concept

    cols = Concept.__table__.columns
    for name in ("source", "material_id", "page_start", "page_end", "summary"):
        assert name in cols, name
    # All of these were added to a table that already had the whole CSW2 and
    # PH101 syllabus in it. A NOT NULL would have broken every existing row.
    for name in ("material_id", "page_start", "page_end", "summary"):
        assert cols[name].nullable, f"{name} must be nullable"


def test_source_defaults_to_seed_on_both_tables():
    """The backfill direction matters more than the default: everything that
    existed when the migration ran was written by seed.py."""
    from app.models import Concept, Topic

    for model in (Concept, Topic):
        assert model.__table__.columns["source"].default.arg == "seed"


def test_deleting_a_book_does_not_delete_the_syllabus_read_out_of_it():
    """ON DELETE SET NULL, never CASCADE. The concept keeps its page range and
    simply stops naming a material."""
    from app.models import Concept

    fk = list(Concept.__table__.columns["material_id"].foreign_keys)[0]
    assert fk.ondelete == "SET NULL"


# ---------------------------------------------------------------------------
# The prune, which would otherwise eat the whole derived syllabus
# ---------------------------------------------------------------------------

def test_the_seed_prune_spares_derived_content():
    """Every derived row is by definition absent from concepts.json -- which is
    exactly the test prune_removed uses to decide what to delete. Without this
    filter the first reset_demo_state.py after a derivation run would silently
    delete the lot, and it would look like the derivation never happened."""
    source = (Path(__file__).resolve().parents[1] / "scripts" / "seed.py").read_text(
        encoding="utf-8"
    )
    body = source[source.index("def prune_removed"):]
    assert body.count('Concept.source == "seed"') == 1
    assert body.count('Topic.source == "seed"') == 1


def test_a_reseed_restamps_seeded_rows_as_seeded():
    """Otherwise a row written before the column existed, or one whose source
    was edited by hand, drifts out of the prune's reach and becomes immortal."""
    source = (Path(__file__).resolve().parents[1] / "scripts" / "seed.py").read_text(
        encoding="utf-8"
    )
    seed_map = source[source.index("def seed_map"):source.index("def seed_users")]
    assert seed_map.count('row.source = "seed"') == 2, "topics AND concepts"


# ---------------------------------------------------------------------------
# The dedupe -- the part a threshold cannot do
# ---------------------------------------------------------------------------

def test_the_merge_is_not_a_similarity_threshold(derive):
    """Measured: restatements of one concept scored 0.7829-0.8625 and different
    concepts 0.4757-0.7970. The bands OVERLAP, so no cut-off separates them.
    See evidence/concept-001/dedupe-calibration.txt."""
    assert not hasattr(derive, "DEDUPE_THRESHOLD"), \
        "a single threshold was measured to be impossible here"
    assert derive.MERGE_CANDIDATE == 0.75
    assert "duplicate_of" in _src(derive.derive), "the decider must be called"


def test_the_gate_sits_below_the_floor_of_real_restatements(derive):
    """0.7829 was the lowest similarity between two genuine restatements. A
    gate above it would silently stop the decider from ever seeing them."""
    assert derive.MERGE_CANDIDATE < 0.7829


def test_a_merge_never_rewrites_a_seeded_concept(derive):
    """A human wrote those on purpose, and the golden path depends on their
    exact names."""
    source = _src(derive.derive)
    assert 'best.source == "derived"' in source


def test_a_merge_widens_the_page_range_rather_than_discarding_the_sighting(derive):
    source = _src(derive.derive)
    assert "best.page_start" in source and "best.page_end" in source


def test_the_dedupe_prompt_prefers_the_visible_mistake():
    """A wrong merge deletes a syllabus line and nobody finds out; a wrong split
    leaves a near-duplicate a human can see. The prompt has to say so."""
    text = (Path(__file__).resolve().parents[2] / "prompts" / "concepts_same.md").read_text(
        encoding="utf-8"
    )
    assert "separate lessons" in text
    assert "visible mistake" in text


# ---------------------------------------------------------------------------
# Windowing
# ---------------------------------------------------------------------------

def test_a_window_never_straddles_a_chapter(derive):
    """A window that did would ask the model to name the concepts of two
    unrelated sections at once, and would produce a page range spanning the
    join."""
    chunks = [_Chunk("A")] * 5 + [_Chunk("B")] * 5
    for chapter, group in derive.windows(chunks, 4):
        assert {c.chapter for c in group} == {chapter}


def test_front_matter_is_skipped(derive):
    """The first dry run derived Django overview / Django architecture /
    Request-response cycle from pages 9-15 -- the TABLE OF CONTENTS. A contents
    page is a list of concept names with no teaching behind any of them."""
    labels = ["Preface", "Contents", "Index", "About the Author",
              "(front matter)", "Copyright", "Acknowledgements"]
    for label in labels:
        assert not list(derive.windows([_Chunk(label)] * 4, 2)), label
    # ...and a real chapter is not swallowed by the same rule.
    assert list(derive.windows([_Chunk("Building a Blog Application")] * 4, 2))


def test_slugs_fit_the_column(derive):
    """Concept.slug is String(80) and unique."""
    long_name = "A concept with an extremely long name " * 5
    assert len(derive.slugify(long_name)) <= 80
    assert derive.slugify("Django's MTV / architecture!") == "django-s-mtv-architecture"
    assert derive.slugify("!!!") == "concept"


def test_a_window_failure_does_not_abandon_the_pass(derive):
    """One bad window must not cost the other 241. The corpus is not going
    anywhere and the cache replays every good call on a re-run."""
    source = _src(derive.derive)
    assert "continue" in source[source.index("except (AllProvidersFailed"):]


def test_the_long_run_commits_per_chapter(derive):
    """A single transaction across ~240 model calls means a crash at window 230
    throws away 229 windows, on a database the whole team shares."""
    source = _src(derive.derive)
    assert "chapter != current_chapter" in source
    assert "db.commit()" in source


# ---------------------------------------------------------------------------
# Pagination -- and the two things it must not break
# ---------------------------------------------------------------------------

def test_the_diagnostic_serves_seeded_items_first():
    """THE GOLDEN PATH DEPENDS ON THIS. Page one has to stay exactly the eight
    hand-written questions, in the same order, however many derived items
    exist."""
    source = _src(student.get_diagnostic)
    assert '(Concept.source != "seed")' in source
    order = source[source.index(".order_by("):]
    assert order.index('Concept.source != "seed"') < order.index("DiagnosticItem.id")


def test_the_diagnostic_is_paginated_and_says_how_many_exist():
    source = _src(student.get_diagnostic)
    assert "limit" in inspect.signature(student.get_diagnostic).parameters
    assert '"total": total' in source, "a client must not think 8 is all there is"


def test_mastery_pages_without_handing_back_a_denominator():
    """A total would let a client count the solid concepts on the page and
    divide -- exactly the aggregate score this endpoint exists not to have.
    The existing anti-score tests catch this; the rule is written here too so
    the reason survives."""
    source = _src(student.mastery)
    body = source[source.index("return {"):]
    assert '"has_more"' in body
    for banned in ("total", "count", "score", "percent"):
        assert banned not in body.lower(), banned


def test_mastery_gets_has_more_without_a_second_query():
    """One row more than the page, thrown away. The database is remote and a
    count is a whole round trip -- see perf-001."""
    source = _src(student.mastery)
    assert "size + 1" in source
    assert "func.count()" not in source


def test_mastery_pages_within_topics_not_across_them():
    """Ordering by id alone would make a page a slice cutting across every
    topic at once."""
    source = _src(student.mastery)
    assert "order_by(Concept.topic_id, Concept.id)" in source


def test_the_syllabus_prompt_is_capped():
    """Every concept in that list goes into ONE prompt, so an uncapped list is
    an uncapped prompt."""
    assert student.SYLLABUS_CONCEPT_CAP <= 200
    source = _src(student.syllabus_upload)
    assert "limit(SYLLABUS_CONCEPT_CAP)" in source
    assert '(Concept.source != "seed")' in source, "seeded prerequisites lead"


# ---------------------------------------------------------------------------
# Browsing
# ---------------------------------------------------------------------------

def test_the_concept_browser_is_admin_only_and_paginated():
    source = _src(admin.course_concepts)
    assert "admin_only" in source and "teacher_only" not in source
    assert "min(limit, MAX_CONCEPT_PAGE)" in source
    assert admin.MAX_CONCEPT_PAGE <= 100


def test_the_concept_browser_can_separate_derived_from_seeded():
    """?source=seed is the deliberate syllabus somebody signed off; derived is
    what the book actually contains. Without the filter the page is just long."""
    source = _src(admin.course_concepts)
    assert 'source in ("seed", "derived")' in source
    assert '"by_source"' in source, "a reviewer needs the split without paging"


def test_the_concept_browser_resolves_names_in_batches():
    """perf-001: a per-row lookup of topic and material is two round trips per
    row, and this endpoint returns up to a hundred rows."""
    source = _src(admin.course_concepts)
    # topics, materials, prerequisite courses -- three queries for a whole page.
    assert source.count(".in_(") == 3
    assert "db.get(Topic" not in source and "db.get(Material" not in source


def test_a_derived_concept_can_be_checked_against_its_pages():
    """The provenance chain this whole file exists for -- an answer, a
    citation, a material, the person who uploaded it -- now includes concepts."""
    source = _src(admin.course_concepts)
    for field in ('"material"', '"page_start"', '"page_end"', '"source"'):
        assert field in source, field


# ---------------------------------------------------------------------------
# Diagnostic items for derived concepts
# ---------------------------------------------------------------------------

def test_only_prerequisite_concepts_get_a_diagnostic_item(derive):
    """A question about material this course is about to teach is not a
    diagnostic. Finding it absent is expected, and reporting it as a gap would
    bury the real gaps in noise."""
    source = _src(derive.make_diagnostic_items)
    assert "Concept.prerequisite_course_id.is_not(None)" in source
    assert 'Concept.source == "derived"' in source


def test_an_existing_item_is_never_duplicated(derive):
    """Re-running the pass must add, not double."""
    source = _src(derive.make_diagnostic_items)
    assert "Concept.id.not_in(" in source
    assert "DiagnosticItem.concept_id" in source


def test_a_malformed_question_is_dropped_rather_than_stored(derive):
    """A malformed prerequisite question is a gap invented out of nothing: it
    sends a student a remedial lesson for something they already understand."""
    source = _src(derive.make_diagnostic_items)
    assert "len(options) != 4" in source
    assert "answer not in options" in source
    assert 'data.get("skip")' in source


def test_the_model_may_refuse_to_write_one(derive):
    """The passage may be an installation step or a narrative aside, which a
    student cannot be right or wrong about."""
    text = (Path(__file__).resolve().parents[2] / "prompts" / "diagnostic_item.md").read_text(
        encoding="utf-8"
    )
    assert '"skip": true' in text
    assert "worse than no question" in text


def test_a_prerequisite_question_cannot_lean_on_the_book_s_example():
    """A question only answerable if you remember the blog app in Chapter 1
    tests recall of a tutorial, not understanding of a concept."""
    text = (Path(__file__).resolve().parents[2] / "prompts" / "diagnostic_item.md").read_text(
        encoding="utf-8"
    )
    assert "running example" in text
    assert "not an exam" in text


# ---------------------------------------------------------------------------
# The prerequisite question, which the first prompt could not answer
# ---------------------------------------------------------------------------

def test_the_prerequisite_question_names_the_prior_course_and_the_subject():
    """Asked in the abstract -- "is this a prerequisite?" -- the model answered
    `false` for Python class inheritance, which is one of the hand-written
    prerequisites this very course tests. Nothing was ever marked true, so the
    whole diagnostic half of the feature was dead. The question only works
    against a named prior course and a named subject."""
    text = (Path(__file__).resolve().parents[2] / "prompts" / "concepts_derive.md").read_text(
        encoding="utf-8"
    )
    assert "{{prerequisite_course}}" in text
    assert "{{subject}}" in text
    # The rule that was wrong: "false for anything the book is actually
    # teaching". A book teaches everything in it, so that answer is always no.
    assert "The book explains everything in" in text
    assert "book is actually teaching" not in text


def test_the_derivation_supplies_both_placeholders(derive):
    source = _src(derive.derive)
    assert "prerequisite_course=" in source and "subject=course.title" in source


# ---------------------------------------------------------------------------
# Re-running from scratch
# ---------------------------------------------------------------------------

def test_a_reset_never_deletes_anything_with_dependents(derive):
    """The same rule prune_removed follows, for the same reason: a concept
    carrying a gap, a mastery row, a practice item or a diagnostic item has real
    history behind it, and a re-derivation is not the authority to discard it."""
    source = _src(derive.reset_derived)
    for dep in ("Gap.concept_id", "Mastery.concept_id",
                "PracticeItem.concept_id", "DiagnosticItem.concept_id"):
        assert dep in source, dep
    assert "KEPT" in source


def test_a_reset_never_touches_seeded_content(derive):
    source = _src(derive.reset_derived)
    assert source.count('Concept.source == "derived"') == 1
    assert source.count('Topic.source == "derived"') == 1
    assert '"seed"' not in source


def test_a_reset_only_drops_topics_that_are_now_empty(derive):
    """A derived topic still holding a kept concept must survive, or that
    concept is orphaned."""
    source = _src(derive.reset_derived)
    assert "Concept.topic_id == t.id" in source
