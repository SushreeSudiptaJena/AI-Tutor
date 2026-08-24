"""rag-004 tests. No network, no database.

Most of these assert that the guardrail does **not** fire. That is the right
balance: a guardrail that refuses homework is easy, and a guardrail that still
teaches the student who came to understand their homework is the actual feature.
Every false-refusal path gets its own test because a false refusal is invisible
in aggregate -- it looks like a student who asked a bad question.
"""

from __future__ import annotations

import inspect
import json

import pytest

from app.services import guardrail, retrieval, tutor
from app.services.retrieval import Hit

ASSIGNMENT_TEXT = (
    "Q3. Create a custom model manager named PublishedManager that overrides "
    "the default queryset to return only posts with status Published."
)


def hit(similarity: float, *, material_id=9, title="Assignment 1 - Chapter 1",
        kind="assignment", text=ASSIGNMENT_TEXT, page_no=2) -> Hit:
    return Hit(chunk_id=1, material_id=material_id, book_title=title, kind=kind,
               page_no=page_no, chapter=None, text=text, similarity=similarity)


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = 1


@pytest.fixture
def llm(monkeypatch):
    """Records every prompt the guardrail sends, so 'no model call' is testable."""
    class Recorder:
        def __init__(self):
            self.prompts = []
            self.reply = json.dumps({"intent": "understand", "confidence": 0.9})

        def __call__(self, prompt, **kwargs):
            self.prompts.append(prompt)
            from app.providers.base import Completion

            text = self.reply(prompt) if callable(self.reply) else self.reply
            return Completion(text=text, provider="fake", model="fake-1")

    rec = Recorder()
    monkeypatch.setattr(guardrail, "complete", rec)
    return rec


@pytest.fixture
def assignments(monkeypatch):
    holder = {"hits": []}
    monkeypatch.setattr(guardrail.retrieval, "search_assignments",
                        lambda *a, **k: holder["hits"])
    return holder


# ---------------------------------------------------------------------------
# The cheap gate runs first
# ---------------------------------------------------------------------------

def test_a_question_matching_no_assignment_costs_no_model_call(llm, assignments):
    assignments["hits"] = []
    v = guardrail.check(FakeDB(), "What is a Django model?", course_id=5)
    assert not v.refuse
    assert llm.prompts == []


def test_a_weak_assignment_match_costs_no_model_call(llm, assignments):
    """Most questions are not homework. They must not each pay for an intent
    call to establish that."""
    assignments["hits"] = [hit(0.62)]
    v = guardrail.check(FakeDB(), "How do querysets work?", course_id=5)
    assert not v.refuse
    assert llm.prompts == []
    assert v.similarity == 0.62


def test_the_intent_call_happens_only_above_the_similarity_gate(llm, assignments):
    assignments["hits"] = [hit(0.93)]
    guardrail.check(FakeDB(), ASSIGNMENT_TEXT, course_id=5)
    assert len(llm.prompts) == 1


# ---------------------------------------------------------------------------
# Both signals required
# ---------------------------------------------------------------------------

def test_solve_intent_on_a_close_match_refuses(llm, assignments):
    assignments["hits"] = [hit(0.93)]
    llm.reply = json.dumps({"intent": "solve", "confidence": 0.95,
                            "reason": "wants the code"})
    v = guardrail.check(FakeDB(), ASSIGNMENT_TEXT + " write this for me", course_id=5)
    assert v.refuse
    assert v.matched_assignment == {"material_id": 9, "title": "Assignment 1 - Chapter 1"}


def test_understand_intent_on_the_same_question_does_not_refuse(llm, assignments):
    """The contrast that makes this a tutor rather than a filter: the same
    assignment text, asked about rather than asked for."""
    assignments["hits"] = [hit(0.93)]
    llm.reply = json.dumps({"intent": "understand", "confidence": 0.95})
    v = guardrail.check(FakeDB(), "Why does this need a custom manager?", course_id=5)
    assert not v.refuse
    assert v.intent == "understand"


# ---------------------------------------------------------------------------
# Ties go to answering
# ---------------------------------------------------------------------------

def test_low_confidence_solve_does_not_refuse(llm, assignments):
    """A guess must not block a student, and they cannot appeal it."""
    assignments["hits"] = [hit(0.93)]
    llm.reply = json.dumps({"intent": "solve", "confidence": 0.3})
    assert not guardrail.check(FakeDB(), ASSIGNMENT_TEXT, course_id=5).refuse


def test_an_unreadable_intent_reply_does_not_refuse(llm, assignments):
    """A provider hiccup turning the tutor into a stonewall is the worst
    failure this system has."""
    assignments["hits"] = [hit(0.93)]
    llm.reply = "I'm sorry, I can't help with that"
    v = guardrail.check(FakeDB(), ASSIGNMENT_TEXT, course_id=5)
    assert not v.refuse
    assert v.intent == "understand"


def test_an_unexpected_intent_value_does_not_refuse(llm, assignments):
    assignments["hits"] = [hit(0.93)]
    llm.reply = json.dumps({"intent": "cheat", "confidence": 0.99})
    assert not guardrail.check(FakeDB(), ASSIGNMENT_TEXT, course_id=5).refuse


def test_similarity_exactly_at_the_gate_does_not_refuse(llm, assignments):
    assignments["hits"] = [hit(guardrail.ASSIGNMENT_SIMILARITY)]
    assert not guardrail.check(FakeDB(), ASSIGNMENT_TEXT, course_id=5).refuse
    assert llm.prompts == []


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------

def test_hints_are_capped(llm):
    llm.reply = json.dumps({"hints": [f"step {i}" for i in range(20)]})
    assert len(guardrail.hints("q", [hit(0.9, kind="textbook")])) == guardrail.MAX_HINTS


def test_unreadable_hints_degrade_to_none_rather_than_raising(llm):
    """A broken hints call must not turn a correct refusal into a 500."""
    llm.reply = "no json here"
    assert guardrail.hints("q", [hit(0.9, kind="textbook")]) == []


def test_the_hints_prompt_forbids_the_solution():
    from app import prompts

    text = prompts.load("guardrail_hints").lower()
    assert "no solution" in text
    assert "no finished code" in text


# ---------------------------------------------------------------------------
# Scope: /tutor/ask only
# ---------------------------------------------------------------------------

def test_a_gap_lesson_never_runs_the_guardrail():
    """A gap lesson is concept-driven -- the student typed nothing -- so there
    is no request-for-the-solution to detect and a refusal is always wrong."""
    source = inspect.getsource(tutor.lesson)
    body = source[source.index('"""', source.index('"""') + 3):]
    assert "guardrail.check" not in body


def test_ask_returns_the_contract_shape_for_a_refusal(llm, assignments, monkeypatch):
    lesson_hits = [hit(0.7, kind="textbook", title="Django 5 By Example",
                       material_id=12, page_no=88, text="Model managers...")]
    monkeypatch.setattr(tutor.retrieval, "search", lambda *a, **k: lesson_hits)
    monkeypatch.setattr(tutor, "complete", llm)
    assignments["hits"] = [hit(0.93)]
    llm.reply = lambda p: (
        json.dumps({"intent": "solve", "confidence": 0.95})
        if "intent check" in p.lower()
        else json.dumps({"hints": ["Start with the manager class."]})
    )

    out = tutor.ask(FakeDB(), ASSIGNMENT_TEXT, course_id=5)

    assert out["outcome"] == "graded_work_refused"
    assert out["hints"] == ["Start with the manager class."]
    assert out["matched_assignment"]["title"] == "Assignment 1 - Chapter 1"
    # Citations still point at real teaching material, so the refusal is useful.
    assert out["citations"][0]["book_title"] == "Django 5 By Example"


def test_a_refusal_never_contains_a_generated_answer(llm, assignments, monkeypatch):
    """The refusal path must not reach the answer prompt at all -- generating
    prose and then discarding it is how a solution leaks into a log."""
    monkeypatch.setattr(tutor.retrieval, "search",
                        lambda *a, **k: [hit(0.7, kind="textbook")])
    monkeypatch.setattr(tutor, "complete", llm)
    assignments["hits"] = [hit(0.93)]
    llm.reply = lambda p: (
        json.dumps({"intent": "solve", "confidence": 0.95})
        if "intent check" in p.lower() else json.dumps({"hints": ["a step"]})
    )

    out = tutor.ask(FakeDB(), ASSIGNMENT_TEXT, course_id=5)

    assert out["outcome"] == "graded_work_refused"
    assert not any("Tutor answer" in p for p in llm.prompts)
