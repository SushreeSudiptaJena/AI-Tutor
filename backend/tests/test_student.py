"""student-001 / student-002 / student-003 tests. No network, no database.

The guarantees worth testing here are mostly *absences* -- no score, no answer
key, no other student's data -- and an absence is exactly what nobody notices
regressing. So they are asserted explicitly rather than left to review.
"""

from __future__ import annotations

import inspect
import json

import pytest

from app.routers import student
from app.schemas import DiagnosticSubmitIn
from app.services import evidence, retrieval, tutor
from app.services.retrieval import Hit


# ---------------------------------------------------------------------------
# The anti-surveillance guarantees, as tests
# ---------------------------------------------------------------------------

def test_the_diagnostic_response_carries_no_score_or_grade():
    """'A gap list, not a grade' is a judging point. The response builder must
    not contain a count of correct answers for a frontend to render."""
    source = inspect.getsource(student.submit_diagnostic)
    body = source[source.index("return {"):]
    for banned in ("score", "percent", "grade", "correct_count", "total"):
        assert banned not in body.lower(), f"{banned!r} leaked into the submit response"


def test_submit_payload_has_no_field_a_score_could_be_built_from():
    fields = set(DiagnosticSubmitIn.model_fields)
    assert fields == {"answers"}


def test_the_diagnostic_never_serialises_the_answer_key():
    source = inspect.getsource(student.get_diagnostic)
    body = source[source.index("return {"):]
    assert "correct_answer" not in body


def test_gap_output_exposes_no_user_id():
    """A gap belongs to a student; the object handed to the browser should not
    restate whose it is."""
    source = inspect.getsource(student._gap_out)
    body = source[source.index("return {"):]
    assert "user_id" not in body


# ---------------------------------------------------------------------------
# Suggested prompts
# ---------------------------------------------------------------------------

def test_suggested_prompts_are_built_without_a_model_call():
    """A dozen gaps must not cost a dozen LLM calls to phrase a button."""
    assert "complete" not in inspect.getsource(student._suggested_prompts)


def test_suggested_prompts_mention_the_concept():
    out = student._suggested_prompts("Vector components", "Vectors and Forces")
    assert len(out) == 3
    assert all("vector components" in p.lower() for p in out[:1])
    assert any("vectors and forces" in p.lower() for p in out)


def test_suggested_prompts_survive_a_concept_with_no_topic():
    assert student._suggested_prompts("Friction", None)


# ---------------------------------------------------------------------------
# Answer matching
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("given,stored", [
    ("12 N", "12 N"),
    (" 12 N ", "12 N"),
    ("12  N", "12 N"),
    ("12 n", "12 N"),
])
def test_answer_matching_ignores_case_and_whitespace(given, stored):
    """The options are strings the student clicks, and a trailing space from
    the seed file must not mark a right answer wrong."""
    assert student._normalise_answer(given) == student._normalise_answer(stored)


def test_answer_matching_does_not_conflate_different_answers():
    assert student._normalise_answer("12 N") != student._normalise_answer("120 N")


def test_duplicate_answers_for_one_item_are_rejected():
    with pytest.raises(ValueError):
        DiagnosticSubmitIn(answers=[{"item_id": 1, "answer": "a"},
                                    {"item_id": 1, "answer": "b"}])


def test_an_empty_submission_is_rejected():
    with pytest.raises(ValueError):
        DiagnosticSubmitIn(answers=[])


# ---------------------------------------------------------------------------
# student-003 -- the gap lesson
# ---------------------------------------------------------------------------

def hit(similarity: float, *, chunk_id=1, page_no=141, text="the text") -> Hit:
    return Hit(chunk_id=chunk_id, material_id=1, book_title="Concepts of Physics, Vol 1",
               kind="textbook", page_no=page_no, chapter="5. Newton's Laws",
               text=text, similarity=similarity)


class FakeDB:
    def __init__(self):
        self.added = []
        self._next_id = 70

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = self._next_id
                self._next_id += 1


@pytest.fixture
def fake_llm(monkeypatch):
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


@pytest.fixture
def patched_search(monkeypatch):
    holder = {"hits": []}
    monkeypatch.setattr(retrieval, "search", lambda *a, **k: holder["hits"])
    monkeypatch.setattr(tutor.retrieval, "search", lambda *a, **k: holder["hits"])
    return holder


def test_a_gap_lesson_is_answered_with_an_alignment_score_and_citations(fake_llm, patched_search):
    patched_search["hits"] = [hit(0.88, page_no=141), hit(0.84, page_no=143)]
    fake_llm.reply = lambda p: (
        json.dumps({"entailment": 0.9, "reason": "covered"})
        if "Evidence check" in p else "A component is the projection along an axis [1]."
    )
    out = tutor.lesson(FakeDB(), "Vector components", course_id=2,
                       topic_name="Vectors and Forces")

    assert out["outcome"] == "answered"
    assert out["evidence"]["alignment_percent"] > 70
    assert [c["page_no"] for c in out["citations"]] == [141, 143]
    assert out["citations"][0]["book_title"] == "Concepts of Physics, Vol 1"


def test_a_gap_lesson_is_never_graded_work_refused(fake_llm, patched_search):
    """The student clicked a gap; they typed nothing. There is no 'asking for
    the solution' to detect, so a guardrail refusal here is always wrong."""
    patched_search["hits"] = [hit(0.88)]
    out = tutor.lesson(FakeDB(), "Newton's second law", course_id=2)
    assert out["outcome"] != "graded_work_refused"


def test_the_lesson_prompt_is_the_lesson_prompt_not_the_chat_one(fake_llm, patched_search):
    """A remedial lesson and a chat answer are different jobs; using the chat
    prompt here would open with 'great question'."""
    patched_search["hits"] = [hit(0.88)]
    tutor.lesson(FakeDB(), "Friction", course_id=2)
    answer_prompt = fake_llm.prompts[-1]
    assert "Gap lesson" in answer_prompt
    assert "Concept to teach" in answer_prompt


def test_a_prerequisite_the_corpus_cannot_teach_refuses_and_is_flagged(fake_llm, patched_search):
    """'We test it but we cannot teach it' is exactly what a teacher needs to
    see, so it must flag rather than improvise."""
    from app.models import UncertaintyFlag

    patched_search["hits"] = [hit(0.40)]
    db = FakeDB()
    out = tutor.lesson(db, "Tensor calculus", course_id=2)

    assert out["outcome"] == "insufficient_evidence"
    assert out["citations"] == []
    flags = [o for o in db.added if isinstance(o, UncertaintyFlag)]
    assert len(flags) == 1
    assert "Tensor calculus" in flags[0].question
    assert out["uncertainty_flag_id"] == flags[0].id


def test_the_lesson_query_names_the_concept_and_its_topic(fake_llm, monkeypatch):
    """A bare concept slug retrieves badly; the topic is the context that makes
    'components' mean vector components rather than software components."""
    seen = {}

    def capture(db, query, **kwargs):
        seen["query"] = query
        return [hit(0.88)]

    monkeypatch.setattr(tutor.retrieval, "search", capture)
    tutor.lesson(FakeDB(), "Vector components", course_id=2, topic_name="Vectors and Forces")

    assert "Vector components" in seen["query"]
    assert "Vectors and Forces" in seen["query"]


# ---------------------------------------------------------------------------
# The options shape the contract promises
# ---------------------------------------------------------------------------

def test_options_are_a_list_of_strings_not_the_stored_wrapper():
    """The column stores {"choices": [...]} so future item kinds can carry more
    without a migration. Shipping that dict put the literal string "choices"
    into the frontend's option list -- not a wrong answer, a broken one."""
    assert student._options_list({"choices": ["a", "b"]}) == ["a", "b"]


def test_options_survive_a_plain_list_and_a_missing_value():
    assert student._options_list(["a", "b"]) == ["a", "b"]
    assert student._options_list(None) is None
    assert student._options_list({}) is None
    assert student._options_list({"choices": "not a list"}) is None


def test_the_diagnostic_route_unwraps_options():
    source = inspect.getsource(student.get_diagnostic)
    assert '"options": _options_list(' in source


# ---------------------------------------------------------------------------
# student-007 -- the mastery view, and the things it must never contain
# ---------------------------------------------------------------------------

def test_the_mastery_view_has_no_aggregate_score():
    """The anti-surveillance stance, as a test. A single number invites
    ranking students against each other and tells nobody what to do next."""
    source = inspect.getsource(student.mastery)
    body = source[source.index("return {"):]
    for banned in ("score", "percent", "grade", "average", "total", "count"):
        assert banned not in body.lower(), f"{banned!r} leaked into the mastery response"


def test_the_mastery_view_exposes_no_timing_or_attempt_tallies():
    """Time-on-task measures compliance, not understanding. The guarantee is
    only real if a frontend cannot rebuild one, so nothing countable ships."""
    source = inspect.getsource(student.mastery)
    body = source[source.index("return {"):]
    for banned in ("updated_at", "time", "duration", "attempts", "seconds"):
        assert banned not in body.lower(), f"{banned!r} leaked into the mastery response"


def test_the_mastery_view_is_scoped_to_the_signed_in_users_course():
    source = inspect.getsource(student.mastery)
    assert "Topic.course_id == course.id" in source
    assert "Mastery.user_id == user.id" in source


def test_a_concept_nobody_has_been_asked_about_is_untested_not_missing():
    """`untested` is a first-class state. Dropping the concept would imply
    competence by omission; a zero would imply failure."""
    source = inspect.getsource(student.mastery)
    assert 'states.get(concept.id, "untested")' in source


def test_mastery_reads_every_state_in_one_query_not_one_per_concept():
    source = inspect.getsource(student.mastery)
    assert source.count("select(Mastery)") == 1
