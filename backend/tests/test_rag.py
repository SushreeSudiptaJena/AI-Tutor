"""rag-001 / rag-002 / rag-003 tests. No network, no database.

The database is faked at the `Session.execute` boundary rather than mocked at
the service boundary, so the real SQLAlchemy statement is still built and can be
inspected. That is what lets us assert the two rules that are invisible in a
passing demo but fatal in a live one: every search is scoped to a course, and
assignments are never quotable.

The provider is faked at `evidence.complete` / `tutor.complete`, which is the
one seam every model call goes through.
"""

from __future__ import annotations

import json

import pytest

from app.models import UncertaintyFlag
from app.services import evidence, retrieval, tutor
from app.services.retrieval import Hit


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeRows:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeDB:
    """Records the statement it was handed, returns canned rows."""

    def __init__(self, rows=()):
        self.rows = list(rows)
        self.statements = []
        self.added = []
        self._next_id = 55

    def execute(self, statement):
        self.statements.append(statement)
        return FakeRows(self.rows)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = self._next_id
                self._next_id += 1

    @property
    def sql(self) -> str:
        return str(self.statements[-1])


class FakeChunk:
    def __init__(self, id, page_no, text, chapter=None):
        self.id, self.page_no, self.text, self.chapter = id, page_no, text, chapter


class FakeMaterial:
    def __init__(self, id, title, kind="textbook"):
        self.id, self.title, self.kind = id, title, kind


def hit(similarity: float, *, chunk_id=1, material_id=4, page_no=143,
        title="Practical C Programming", chapter=None, text="the text") -> Hit:
    return Hit(chunk_id=chunk_id, material_id=material_id, book_title=title,
               kind="textbook", page_no=page_no, chapter=chapter, text=text,
               similarity=similarity)


@pytest.fixture(autouse=True)
def no_embedding(monkeypatch):
    """Never load the ONNX model in the test suite."""
    monkeypatch.setattr(retrieval, "embed_query", lambda q: [0.0] * 384)


@pytest.fixture
def fake_llm(monkeypatch):
    """Swap the provider seam. Returns a recorder with the prompts it saw."""
    class Recorder:
        def __init__(self):
            self.prompts = []
            self.reply = json.dumps({"entailment": 0.9, "reason": "covered"})

        def __call__(self, prompt, **kwargs):
            self.prompts.append(prompt)
            from app.providers.base import Completion

            text = self.reply(prompt) if callable(self.reply) else self.reply
            return Completion(text=text, provider="fake", model="fake-1")

    rec = Recorder()
    monkeypatch.setattr(evidence, "complete", rec)
    monkeypatch.setattr(tutor, "complete", rec)
    return rec


# ---------------------------------------------------------------------------
# rag-001 -- retrieval
# ---------------------------------------------------------------------------

def test_search_is_scoped_to_one_course():
    """Several courses' books share one database. An unscoped search returns a
    plausible answer with a real citation from the wrong subject -- which reads
    as a slightly odd answer, not as a bug, and would survive a rehearsal."""
    db = FakeDB()
    retrieval.search(db, "what is a pointer?", course_id=7)
    assert "materials.course_id" in db.sql


def _params(db: "FakeDB") -> dict:
    return db.statements[-1].compile().params


def test_search_never_returns_assignment_material():
    """Graded material stays searchable so the guardrail can recognise it, but
    it can never be handed back to a student as a lesson."""
    db = FakeDB()
    retrieval.search(db, "solve question 3", course_id=7)
    assert "assignment" not in _params(db)["kind_1"]
    assert set(_params(db)["kind_1"]) == set(retrieval.LESSON_KINDS)


def test_search_assignments_returns_only_assignment_material():
    db = FakeDB()
    retrieval.search_assignments(db, "solve question 3", course_id=7)
    assert _params(db)["kind_1"] == ["assignment"]


def test_search_excludes_archived_material_by_default():
    """An archived material is a superseded edition; citing it points a student
    at a page their current book does not have."""
    db = FakeDB()
    retrieval.search(db, "q", course_id=7)
    assert _params(db).get("status_1") == "active"

    db = FakeDB()
    retrieval.search(db, "q", course_id=7, include_archived=True)
    assert "status_1" not in _params(db)


def test_similarity_is_one_minus_cosine_distance():
    db = FakeDB([(FakeChunk(1, 143, "body"), FakeMaterial(4, "Book"), 0.2)])
    hits = retrieval.search(db, "q", course_id=7)
    assert len(hits) == 1
    assert hits[0].similarity == pytest.approx(0.8)
    assert hits[0].page_no == 143


def test_citation_carries_book_and_page_from_stored_columns():
    """No model is asked where a passage came from, so a citation cannot be
    hallucinated -- it is copied off the chunk row ingestion wrote."""
    c = hit(0.9, chunk_id=812, material_id=4, page_no=143,
            chapter="5. Pointers", text="A pointer holds an address.").citation()
    assert c == {
        "chunk_id": 812, "material_id": 4, "book_title": "Practical C Programming",
        "page_no": 143, "chapter": "5. Pointers",
        "snippet": "A pointer holds an address.",
    }


def test_citations_are_deduplicated_per_page():
    """Overlapping chunks off one page must not render as two sources."""
    hits = [hit(0.9, chunk_id=1, page_no=143), hit(0.8, chunk_id=2, page_no=143),
            hit(0.7, chunk_id=3, page_no=144)]
    assert [c["page_no"] for c in retrieval.citations(hits)] == [143, 144]


def test_snippet_is_cut_at_a_word_boundary():
    out = retrieval.snippet("alpha beta gamma delta epsilon", limit=12)
    assert out.endswith("...")
    assert "gam..." not in out


def test_context_block_labels_every_passage_with_its_source():
    block = retrieval.context_block([hit(0.9, page_no=143, chapter="5. Pointers")])
    assert "[1]" in block and "page 143" in block and "5. Pointers" in block


def test_context_block_stops_at_the_character_budget():
    hits = [hit(0.9, chunk_id=i, page_no=i, text="x" * 500) for i in range(1, 21)]
    assert len(retrieval.context_block(hits, max_chars=1200)) <= 1200


# ---------------------------------------------------------------------------
# rag-002 -- evidence and the alignment score
# ---------------------------------------------------------------------------

def test_well_covered_topic_scores_high(fake_llm):
    report = evidence.assess("what is a pointer?", [hit(0.85), hit(0.80), hit(0.78)])
    assert report.sufficient
    assert report.alignment_percent > 70
    assert report.reason is None


def test_tangential_topic_scores_visibly_lower(fake_llm):
    fake_llm.reply = json.dumps({"entailment": 0.2, "reason": "adjacent topic only"})
    covered = evidence.assess("covered", [hit(0.85), hit(0.80)])

    fake_llm.reply = json.dumps({"entailment": 0.9, "reason": "covered"})
    strong = evidence.assess("covered", [hit(0.85), hit(0.80)])

    assert strong.alignment_percent - covered.alignment_percent >= 20


def test_high_similarity_but_no_entailment_still_refuses(fake_llm):
    """The case similarity alone cannot catch: a near-domain question that
    retrieves confident-looking passages which do not answer it."""
    fake_llm.reply = json.dumps({"entailment": 0.15, "reason": "does not cover recursion"})
    report = evidence.assess("explain recursion", [hit(0.90), hit(0.88)])
    assert not report.sufficient
    assert report.reason == evidence.NOT_ENTAILED


def test_low_similarity_refuses_even_when_entailment_is_high(fake_llm):
    report = evidence.assess("who won the 2018 world cup?", [hit(0.40)])
    assert not report.sufficient
    assert report.reason == evidence.NO_MATERIAL


def test_no_hits_refuses_without_spending_an_llm_call(fake_llm):
    report = evidence.assess("anything", [])
    assert not report.sufficient
    assert report.reason == evidence.NO_MATERIAL
    assert report.alignment_percent == 0
    assert fake_llm.prompts == []


def test_unreadable_entailment_reply_fails_closed(fake_llm):
    """A provider outage must not become a confidently wrong answer."""
    fake_llm.reply = "I'm sorry, I can't do that"
    report = evidence.assess("what is a pointer?", [hit(0.90)])
    assert report.entailment == 0.0
    assert not report.sufficient


def test_entailment_out_of_range_is_clamped(fake_llm):
    fake_llm.reply = json.dumps({"entailment": 7.5, "reason": "over-eager"})
    assert evidence.assess("q", [hit(0.9)]).entailment == 1.0


def test_retrieval_score_weights_are_renormalised_over_the_hits_present():
    """Two hits must not be penalised against three just because a weight went
    unused."""
    assert evidence.retrieval_score([hit(0.8)]) == pytest.approx(0.8)
    assert evidence.retrieval_score([hit(0.8), hit(0.8)]) == pytest.approx(0.8)
    assert evidence.retrieval_score([]) == 0.0


def test_report_dict_exposes_only_the_contract_fields(fake_llm):
    keys = set(evidence.assess("q", [hit(0.9)]).to_dict())
    assert keys == {"alignment_score", "alignment_percent", "top_similarity",
                    "threshold", "sufficient", "reason"}


def test_entailment_prompt_is_given_the_passages_not_just_the_question(fake_llm):
    evidence.assess("what is a pointer?", [hit(0.9, text="A pointer holds an address.")])
    assert "A pointer holds an address." in fake_llm.prompts[0]


# ---------------------------------------------------------------------------
# rag-003 -- refusal and the uncertainty flag
# ---------------------------------------------------------------------------

@pytest.fixture
def patched_search(monkeypatch):
    """Control what retrieval returns without a database."""
    holder = {"hits": []}
    monkeypatch.setattr(retrieval, "search", lambda *a, **k: holder["hits"])
    monkeypatch.setattr(tutor.retrieval, "search", lambda *a, **k: holder["hits"])
    return holder


def test_off_syllabus_question_refuses_and_does_not_fabricate(fake_llm, patched_search):
    patched_search["hits"] = [hit(0.42)]
    db = FakeDB()
    out = tutor.ask(db, "who won the 2018 world cup?", course_id=7)

    assert out["outcome"] == "insufficient_evidence"
    assert out["citations"] == []
    assert out["evidence"]["sufficient"] is False
    # Only the entailment call was made; no answer was ever generated.
    assert len(fake_llm.prompts) <= 1


def test_refusal_writes_an_uncertainty_flag_the_teacher_panel_can_read(fake_llm, patched_search):
    patched_search["hits"] = [hit(0.42)]
    db = FakeDB()
    out = tutor.ask(db, "who won the 2018 world cup?", course_id=7, topic_id=12)

    flags = [o for o in db.added if isinstance(o, UncertaintyFlag)]
    assert len(flags) == 1
    flag = flags[0]
    assert flag.question == "who won the 2018 world cup?"
    assert flag.reason == evidence.NO_MATERIAL
    assert flag.course_id == 7 and flag.topic_id == 12
    assert flag.status == "open"
    assert out["uncertainty_flag_id"] == flag.id


def test_the_flag_cannot_identify_the_student_who_asked(fake_llm, patched_search):
    """teacher-004 must be anonymous, and the cheapest guarantee is never
    recording the link."""
    patched_search["hits"] = [hit(0.42)]
    db = FakeDB()
    tutor.ask(db, "off syllabus", course_id=7)
    flag = [o for o in db.added if isinstance(o, UncertaintyFlag)][0]
    assert not hasattr(flag, "user_id")


def test_a_covered_question_is_answered_with_citations(fake_llm, patched_search):
    patched_search["hits"] = [hit(0.88, page_no=143), hit(0.84, page_no=144)]
    fake_llm.reply = lambda prompt: (
        json.dumps({"entailment": 0.92, "reason": "covered"})
        if "Evidence check" in prompt else "A pointer holds an address [1]."
    )
    db = FakeDB()
    out = tutor.ask(db, "what is a pointer?", course_id=7)

    assert out["outcome"] == "answered"
    assert out["body"] == "A pointer holds an address [1]."
    assert [c["page_no"] for c in out["citations"]] == [143, 144]
    assert out["evidence"]["sufficient"] is True
    assert not any(isinstance(o, UncertaintyFlag) for o in db.added)


def test_an_answered_response_always_carries_at_least_one_citation(fake_llm, patched_search):
    """'Never empty on an answered response' -- the whole point of the build."""
    patched_search["hits"] = [hit(0.88)]
    out = tutor.ask(FakeDB(), "what is a pointer?", course_id=7)
    assert out["outcome"] == "answered"
    assert out["citations"]


def test_answered_response_has_no_uncertainty_flag_id(fake_llm, patched_search):
    patched_search["hits"] = [hit(0.88)]
    assert "uncertainty_flag_id" not in tutor.ask(FakeDB(), "q", course_id=7)


def test_the_guardrail_outcome_is_not_reachable_from_this_service(fake_llm, patched_search):
    """graded_work_refused belongs to rag-004 and to /tutor/ask only. A gap
    lesson is concept-driven, so a refusal there could only be a false
    positive."""
    patched_search["hits"] = [hit(0.88)]
    assert tutor.ask(FakeDB(), "solve question 3", course_id=7)["outcome"] == "answered"


def test_language_reports_what_was_actually_produced(fake_llm, patched_search,
                                                     monkeypatch):
    """Claiming 'hi' while returning English would be a lie the UI renders.

    `translate()` returns its input unchanged when the call fails, so "we asked
    for Hindi" and "we got Hindi" are different facts. The response reports the
    second one. Both directions are patched here rather than left to the real
    provider -- this suite makes no network calls, and before i18n-001 was
    wired this test was quietly reaching Sarvam.
    """
    from app.services import language as lang

    patched_search["hits"] = [hit(0.88)]

    # Translation unavailable -> English, and said so.
    monkeypatch.setattr(lang, "available", lambda: False)
    out = tutor.ask(FakeDB(), "what is a pointer?", course_id=7, language="hi")
    assert out["language"] == "en"
    assert out["outcome"] == "answered"

    # Translation available but a no-op (the failure mode that matters) -> still en.
    monkeypatch.setattr(lang, "available", lambda: True)
    monkeypatch.setattr(lang.translate_sarvam, "translate",
                        lambda text, **kw: text)
    out = tutor.ask(FakeDB(), "what is a pointer?", course_id=7, language="hi")
    assert out["language"] == "en", "an unchanged translation is not a translation"

    # Translation actually happens -> reported as hi.
    monkeypatch.setattr(lang.translate_sarvam, "translate",
                        lambda text, **kw: f"[{kw.get('to')}] {text}")
    out = tutor.ask(FakeDB(), "what is a pointer?", course_id=7, language="hi")
    assert out["language"] == "hi"
    assert out["body"].startswith("[hi] ")


def test_translation_never_touches_citations_or_the_alignment_score(
        fake_llm, patched_search, monkeypatch):
    """The badge must not drift between languages. It is computed on the
    English text, before anything is translated out, and citations name an
    English book and page whatever the student reads in."""
    from app.services import language as lang

    patched_search["hits"] = [hit(0.88)]
    monkeypatch.setattr(lang, "available", lambda: False)
    english = tutor.ask(FakeDB(), "what is a pointer?", course_id=7, language="en")

    monkeypatch.setattr(lang, "available", lambda: True)
    monkeypatch.setattr(lang.translate_sarvam, "translate",
                        lambda text, **kw: f"[{kw.get('to')}] {text}")
    hindi = tutor.ask(FakeDB(), "what is a pointer?", course_id=7, language="hi")

    assert hindi["evidence"] == english["evidence"]
    assert hindi["citations"] == english["citations"]
    assert hindi["body"] != english["body"]


# ---------------------------------------------------------------------------
# Prompt rendering -- the corpus is untrusted text
# ---------------------------------------------------------------------------

def test_c_source_in_the_context_does_not_break_prompt_rendering():
    """`int a[2][2] = {{1,2},{3,4}};` contains {{ and }}. A renderer that
    scanned its own output for leftover placeholders would refuse to build a
    perfectly good prompt -- and this corpus is a C programming book."""
    from app import prompts

    out = prompts.render("evidence_entailment", question="q?",
                         context="int a[2][2] = {{1,2},{3,4}};")
    assert "{{1,2},{3,4}}" in out


def test_a_placeholder_the_caller_forgot_is_an_error():
    from app import prompts

    with pytest.raises(KeyError):
        prompts.render("evidence_entailment", question="q?")


def test_format_style_braces_in_material_are_left_alone():
    """printf("{%d}", n) must survive verbatim; .format() would raise on it."""
    from app import prompts

    out = prompts.render("tutor_answer", question="q?",
                         context='printf("{%d}", n);')
    assert 'printf("{%d}", n);' in out


# ---------------------------------------------------------------------------
# Citation numbering -- prose [n] must be citations[n-1]
# ---------------------------------------------------------------------------

def test_context_numbering_matches_the_citation_list():
    """An answer that says [5] when only four citations came back sends the
    student to a source that does not exist. Observed live before this was
    fixed: five passages, two of them the same page, four citations."""
    hits = [hit(0.9, chunk_id=1, page_no=224, text="alpha"),
            hit(0.8, chunk_id=2, page_no=224, text="beta"),
            hit(0.7, chunk_id=3, page_no=225, text="gamma")]
    context, cites = retrieval.grounding(hits)

    assert len(cites) == 2                      # two distinct pages
    assert "[1]" in context and "[2]" in context
    assert "[3]" not in context
    assert [c["page_no"] for c in cites] == [224, 225]


def test_two_chunks_from_one_page_are_merged_without_repeating_the_overlap():
    """Consecutive chunks share a sentence by design; the prompt must not say
    it twice."""
    a = "The pointer moves forward. " + "x" * 60 + " It then stops."
    b = " It then stops. And the loop ends."
    hits = [hit(0.9, chunk_id=1, page_no=10, text=a),
            hit(0.8, chunk_id=2, page_no=10, text=b)]
    context, _ = retrieval.grounding(hits)
    assert context.count("It then stops") == 1


def test_truncated_context_does_not_leave_an_unsupported_citation():
    """A source the model never saw must not appear under Show Source."""
    hits = [hit(0.9, chunk_id=i, page_no=i, text="x" * 900) for i in range(1, 11)]
    context, cites = retrieval.grounding(hits, max_chars=2000)
    assert len(cites) == context.count("] Practical C Programming")
    assert len(cites) < len(hits)


def test_a_single_oversized_source_is_still_included():
    """The budget must not produce an answered response with zero citations."""
    context, cites = retrieval.grounding([hit(0.9, text="x" * 9000)], max_chars=1000)
    assert len(cites) == 1 and context
