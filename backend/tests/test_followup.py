"""tutor-003 tests. No network, no database.

The feature is a rewrite that runs BEFORE the guardrail, the retrieval query
and the evidence check. So most of what matters here is not "does it rewrite
nicely" -- it is:

  1. that a self-contained question costs nothing at all, and
  2. that every failure path hands back the ORIGINAL question, because the
     worst case has to be today's behaviour rather than the tutor confidently
     answering a question nobody asked, and
  3. that what reaches the guardrail and retrieval is the RESOLVED text, since
     that is the entire reason the rewrite sits where it sits.
"""

from __future__ import annotations

import json

import pytest

from app.models import TutorMessage
from app.services import followup, tutor
from app.services.retrieval import Hit


def student(text: str, course_id: int = 1) -> TutorMessage:
    return TutorMessage(user_id=7, course_id=course_id, role="student", text=text)


def tutor_turn(body: str, course_id: int = 1) -> TutorMessage:
    return TutorMessage(user_id=7, course_id=course_id, role="tutor",
                        response={"outcome": "answered", "body": body})


HISTORY = [
    student("What is a model manager?"),
    tutor_turn("A model manager is the interface through which database query "
               "operations are provided to Django models [1]."),
]


class FakeDB:
    """Enough of a Session for followup._recent() and tutor._remember()."""

    def __init__(self, rows=()):
        self.rows = list(rows)
        self.added = []

    def execute(self, _stmt):
        rows = self.rows
        class Result:
            def scalars(self_inner):
                # _recent() asks newest-first and reverses, so hand back
                # newest-first the way the real query would.
                return list(reversed(rows))
        return Result()

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = 1


@pytest.fixture
def rewriter(monkeypatch):
    """Records prompts, so 'no model call' is a testable assertion."""
    class Recorder:
        def __init__(self):
            self.prompts = []
            self.reply = json.dumps({"standalone": "Explain model managers more simply.",
                                     "rewritten": True})

        def __call__(self, prompt, **kwargs):
            self.prompts.append(prompt)
            from app.providers.base import Completion

            text = self.reply(prompt) if callable(self.reply) else self.reply
            return Completion(text=text, provider="fake", model="fake-1")

    rec = Recorder()
    monkeypatch.setattr(followup, "complete", rec)
    return rec


# --- the cheap gate ---------------------------------------------------------

@pytest.mark.parametrize("question", [
    "explain that more simply",
    "why?",
    "and for a ManyToMany?",
    "go on",
    "can you show me the same in C",
    "What about them?",
])
def test_a_follow_up_is_recognised_as_needing_context(question):
    assert followup._needs_context(question) is True


@pytest.mark.parametrize("question", [
    "What is a model manager in Django?",
    "How do I write a custom QuerySet for a Post model?",
    "Explain the difference between a ForeignKey and a ManyToManyField.",
])
def test_a_self_contained_question_does_not_need_context(question):
    assert followup._needs_context(question) is False


def test_a_self_contained_question_costs_no_model_call_and_no_history_read(rewriter):
    """The common case must be free -- not one query, not one token."""
    class ExplodingDB:
        def execute(self, *a, **k):
            raise AssertionError("history must not be read for a standalone question")

    out = followup.resolve(ExplodingDB(), "What is a model manager in Django?",
                           user_id=7, course_id=1)

    assert out.rewritten is False
    assert out.question == "What is a model manager in Django?"
    assert rewriter.prompts == []


def test_a_stateless_call_is_never_rewritten(rewriter):
    """user_id=None is the contract for the stateless path the older tests use."""
    out = followup.resolve(FakeDB(HISTORY), "explain that more simply",
                           user_id=None, course_id=1)

    assert out.rewritten is False
    assert out.question == "explain that more simply"
    assert rewriter.prompts == []


def test_the_first_message_of_a_conversation_is_not_rewritten(rewriter):
    out = followup.resolve(FakeDB([]), "why?", user_id=7, course_id=1)

    assert out.rewritten is False
    assert out.question == "why?"
    assert rewriter.prompts == [], "nothing to resolve against, so nothing to ask"


# --- the happy path ---------------------------------------------------------

def test_a_follow_up_is_resolved_against_the_conversation(rewriter):
    out = followup.resolve(FakeDB(HISTORY), "explain that more simply",
                           user_id=7, course_id=1)

    assert out.rewritten is True
    assert out.question == "Explain model managers more simply."
    assert out.original == "explain that more simply"


def test_the_prompt_carries_the_earlier_turns(rewriter):
    followup.resolve(FakeDB(HISTORY), "explain that more simply",
                     user_id=7, course_id=1)

    prompt = rewriter.prompts[0]
    assert "What is a model manager?" in prompt
    assert "interface through which database query" in prompt
    assert "explain that more simply" in prompt


def test_a_tutor_answer_is_excerpted_not_pasted_whole(rewriter):
    long_body = "Model managers. " + ("padding " * 400)
    followup.resolve(FakeDB([student("what is it"), tutor_turn(long_body)]),
                     "explain that more simply", user_id=7, course_id=1)

    assert len(rewriter.prompts[0]) < 4000, "the window must not grow with answer length"


# --- every failure path returns the original --------------------------------

def test_a_provider_failure_returns_the_original_question(rewriter):
    def boom(*a, **k):
        raise RuntimeError("provider down")
    rewriter.reply = boom

    out = followup.resolve(FakeDB(HISTORY), "explain that more simply",
                           user_id=7, course_id=1)

    assert out.rewritten is False
    assert out.question == "explain that more simply"


def test_unreadable_json_returns_the_original_question(rewriter):
    rewriter.reply = "I think you meant model managers!"

    out = followup.resolve(FakeDB(HISTORY), "explain that more simply",
                           user_id=7, course_id=1)

    assert out.rewritten is False
    assert out.question == "explain that more simply"


def test_an_empty_rewrite_returns_the_original_question(rewriter):
    rewriter.reply = json.dumps({"standalone": "   ", "rewritten": True})

    out = followup.resolve(FakeDB(HISTORY), "explain that more simply",
                           user_id=7, course_id=1)

    assert out.rewritten is False
    assert out.question == "explain that more simply"


def test_a_history_read_that_fails_returns_the_original_question(rewriter):
    class BrokenDB:
        def execute(self, *a, **k):
            raise RuntimeError("database gone")

    out = followup.resolve(BrokenDB(), "explain that more simply",
                           user_id=7, course_id=1)

    assert out.rewritten is False
    assert out.question == "explain that more simply"


def test_a_rewrite_that_invents_subject_matter_is_rejected(rewriter):
    """The one failure that actually changes the answer.

    Under-resolving leaves today's behaviour. Over-resolving makes the tutor
    answer, and score, a question the student never asked.
    """
    rewriter.reply = json.dumps({
        "standalone": "Explain model managers more simply, " + ("and also cover " * 40),
        "rewritten": True,
    })

    out = followup.resolve(FakeDB(HISTORY), "explain that more simply",
                           user_id=7, course_id=1)

    assert out.rewritten is False
    assert out.question == "explain that more simply"


def test_a_rewriter_that_returns_the_message_unchanged_is_not_a_rewrite(rewriter):
    rewriter.reply = json.dumps({"standalone": "explain that more simply",
                                 "rewritten": False})

    out = followup.resolve(FakeDB(HISTORY), "explain that more simply",
                           user_id=7, course_id=1)

    assert out.rewritten is False


# --- integration: what the rest of the pipeline actually sees ----------------

@pytest.fixture
def pipeline(monkeypatch, rewriter):
    """Wire ask() up with everything downstream stubbed and recorded."""
    seen = {"guardrail": [], "retrieval": [], "evidence": []}

    def fake_check(db, question, *, course_id):
        seen["guardrail"].append(question)
        from app.services.guardrail import Verdict
        return Verdict(refuse=False, similarity=0.1, reason="not graded work")

    def fake_search(db, question, *, course_id, k=6):
        seen["retrieval"].append(question)
        return [Hit(chunk_id=1, material_id=2, book_title="Django Book",
                    kind="textbook", page_no=12, chapter=None,
                    text="A model manager is the interface...", similarity=0.83)]

    def fake_assess(question, hits, relaxed=False):
        seen["evidence"].append(question)
        from app.services.evidence import EvidenceReport
        return EvidenceReport(alignment_score=0.83, alignment_percent=83,
                              top_similarity=0.83, threshold=0.70,
                              sufficient=True)

    monkeypatch.setattr(tutor.guardrail, "check", fake_check)
    monkeypatch.setattr(tutor.retrieval, "search", fake_search)
    monkeypatch.setattr(tutor.evidence, "assess", fake_assess)
    monkeypatch.setattr(tutor, "complete",
                        lambda *a, **k: __import__("app.providers.base", fromlist=["Completion"])
                        .Completion(text="Managers, simply. [1]", provider="fake", model="f"))
    return seen


def test_the_guardrail_and_retrieval_see_the_RESOLVED_question(pipeline):
    """The reason the rewrite sits before the guardrail rather than after it."""
    db = FakeDB(HISTORY)

    tutor.ask(db, "explain that more simply", course_id=1, user_id=7)

    assert pipeline["guardrail"] == ["Explain model managers more simply."]
    assert pipeline["retrieval"] == ["Explain model managers more simply."]
    assert pipeline["evidence"] == ["Explain model managers more simply."]


def test_the_response_reports_what_it_actually_answered(pipeline):
    db = FakeDB(HISTORY)

    out = tutor.ask(db, "explain that more simply", course_id=1, user_id=7)

    assert out["resolved_question"] == "Explain model managers more simply."


def test_resolved_question_is_absent_when_nothing_was_rewritten(pipeline):
    db = FakeDB(HISTORY)

    out = tutor.ask(db, "What is a model manager in Django?", course_id=1, user_id=7)

    assert "resolved_question" not in out, (
        "an unrewritten question must not grow a field the frontend would render"
    )


def test_the_transcript_stores_what_the_student_TYPED(pipeline):
    """The chat is a record of the conversation, not of our rewriting of it."""
    db = FakeDB(HISTORY)

    tutor.ask(db, "explain that more simply", course_id=1, user_id=7)

    typed = [m for m in db.added if getattr(m, "role", None) == "student"]
    assert len(typed) == 1
    assert typed[0].text == "explain that more simply"
