"""student-005 / student-006 tests. No network, no database.

The load-bearing property here is that a wrong answer produces a *specific*
diagnosis. It is easy to build a practice generator whose items look fine and
diagnose nothing, and the failure is silent -- the student answers wrong and is
simply told they were wrong. These tests exist because that is the demo's most
important moment.
"""

from __future__ import annotations

import json

import pytest

from app.providers.mock import MockProvider
from app.services import practice


class FakeMisconception:
    def __init__(self, slug, problem_type, label, pattern=None, id=1):
        self.id = id
        self.slug = slug
        self.problem_type = problem_type
        self.label = label
        self.wrong_answer_pattern = pattern
        self.description = "because reasons"


KNOWN = {
    "sin-cos-swap": FakeMisconception(
        "sin-cos-swap", "resolve-vector-components",
        "Uses sine where cosine is required when resolving along the horizontal",
        r"^5(\.0+)?\s*N$", id=2),
    "velocity-implies-force": FakeMisconception(
        "velocity-implies-force", "net-force-constant-velocity",
        "Treats constant velocity as implying a net force",
        r"^(?!0\s*N).*\d+\s*N", id=1),
}


def item(**over) -> dict:
    base = {
        "prompt": "A force of 14 N acts at 40 degrees above the horizontal. "
                  "What is its horizontal component?",
        "kind": "mcq",
        "options": ["9.0 N", "10.7 N", "14 N", "18.3 N"],
        "correct_answer": "10.7 N",
        "problem_type": "resolve-vector-components",
        "distractors": {"9.0 N": "sin-cos-swap"},
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# Validation -- an item that cannot be diagnosed is not usable
# ---------------------------------------------------------------------------

def test_a_well_formed_item_passes():
    assert practice.validate_item(item(), KNOWN) is None


def test_an_item_whose_wrong_answers_diagnose_nothing_is_rejected():
    """The whole point of the feature. Without this the generator happily
    produces items that look right and teach nothing on a wrong answer."""
    reason = practice.validate_item(item(distractors={}), KNOWN)
    assert reason == "no wrong option maps to a known misconception"


def test_a_distractor_naming_an_unknown_misconception_does_not_count():
    reason = practice.validate_item(item(distractors={"9.0 N": "invented-slug"}), KNOWN)
    assert reason == "no wrong option maps to a known misconception"


def test_mapping_the_correct_answer_to_a_misconception_does_not_count():
    """Marking the right answer as a mistake would diagnose a student who got
    it right."""
    reason = practice.validate_item(item(distractors={"10.7 N": "sin-cos-swap"}), KNOWN)
    assert reason == "no wrong option maps to a known misconception"


def test_a_distractor_that_is_not_one_of_the_options_does_not_count():
    reason = practice.validate_item(item(distractors={"99 N": "sin-cos-swap"}), KNOWN)
    assert reason == "no wrong option maps to a known misconception"


def test_the_correct_answer_must_be_among_the_options():
    assert practice.validate_item(item(correct_answer="7 N"), KNOWN) == \
        "correct_answer is not one of the options"


def test_an_unknown_problem_type_is_rejected():
    """problem_type is the join to misconceptions; an invented one silently
    orphans the item."""
    reason = practice.validate_item(item(problem_type="made-up"), KNOWN)
    assert reason == "unknown problem_type 'made-up'"


def test_duplicate_options_are_rejected():
    assert practice.validate_item(
        item(options=["9.0 N", "9.0 N", "14 N", "18.3 N"]), KNOWN) == "duplicate options"


def test_the_wrong_number_of_options_is_rejected():
    assert "expected 4 options" in practice.validate_item(
        item(options=["9.0 N", "10.7 N"]), KNOWN)


def test_an_empty_prompt_is_rejected():
    assert practice.validate_item(item(prompt="   "), KNOWN) == "empty prompt"


def test_clean_distractors_drops_everything_unusable():
    raw = item(distractors={"9.0 N": "sin-cos-swap", "10.7 N": "sin-cos-swap",
                            "99 N": "sin-cos-swap", "14 N": "nope"})
    assert practice._clean_distractors(raw, KNOWN) == {"9.0 N": "sin-cos-swap"}


# ---------------------------------------------------------------------------
# Diagnosis
# ---------------------------------------------------------------------------

class FakeItem:
    def __init__(self, options, problem_type="resolve-vector-components"):
        self.options = options
        self.problem_type = problem_type
        self.correct_answer = "10.7 N"
        self.prompt = "..."


class FakeDB:
    """Answers the two queries diagnose() makes, by slug and by problem_type."""

    def __init__(self, misconceptions=()):
        self.rows = list(misconceptions)

    def scalar(self, stmt):
        wanted = _slug_in(stmt)
        return next((m for m in self.rows if m.slug == wanted), None)

    def scalars(self, stmt):
        wanted = _problem_type_in(stmt)
        return _Result([m for m in self.rows if m.problem_type == wanted])


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


def _slug_in(stmt) -> str | None:
    params = stmt.compile().params
    return params.get("slug_1")


def _problem_type_in(stmt) -> str | None:
    params = stmt.compile().params
    return params.get("problem_type_1")


def test_a_declared_distractor_diagnoses_exactly(monkeypatch):
    """Generated items carry their own mapping, so a question about 14 N at 40
    degrees diagnoses even though no seeded regex knows those numbers."""
    db = FakeDB(KNOWN.values())
    it = FakeItem({"choices": ["9.0 N", "10.7 N", "14 N", "18.3 N"],
                   "distractors": {"9.0 N": "sin-cos-swap"}})
    found, source = practice.diagnose(db, it, "9.0 N")
    assert found.slug == "sin-cos-swap"
    assert source == "pattern"


def test_a_seeded_regex_still_works_for_seeded_items():
    db = FakeDB(KNOWN.values())
    it = FakeItem({"choices": ["5 N", "8.66 N", "10 N", "11.5 N"]})
    found, _ = practice.diagnose(db, it, "5 N")
    assert found.slug == "sin-cos-swap"


def test_no_match_returns_no_diagnosis():
    """A generic diagnosis is worse than none -- the student is asked to
    confirm reasoning that was never theirs."""
    db = FakeDB(KNOWN.values())
    it = FakeItem({"choices": ["9.0 N", "10.7 N", "14 N", "18.3 N"]})
    found, source = practice.diagnose(db, it, "18.3 N")
    assert found is None
    assert source == "none"


def test_a_misconception_from_another_problem_type_is_never_matched():
    """velocity-implies-force matches almost any answer ending in N. Scoping to
    problem_type is what stops it diagnosing every wrong answer in the app."""
    db = FakeDB(KNOWN.values())
    it = FakeItem({"choices": ["9.0 N", "10.7 N", "14 N", "18.3 N"]},
                  problem_type="resolve-vector-components")
    found, _ = practice.diagnose(db, it, "18.3 N")
    assert found is None


def test_a_broken_regex_in_seed_data_does_not_raise():
    broken = FakeMisconception("bad", "resolve-vector-components", "x", "([unclosed")
    db = FakeDB([broken])
    it = FakeItem({"choices": ["9.0 N"]})
    assert practice.diagnose(db, it, "9.0 N") == (None, "none")


# ---------------------------------------------------------------------------
# Answer matching and the confirm question
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("given", ["0 N", " 0 N ", "0  n"])
def test_correctness_ignores_case_and_spacing(given):
    assert practice.is_correct(given, "0 N")


def test_correctness_does_not_conflate_similar_answers():
    assert not practice.is_correct("10 N", "0 N")


def test_the_confirm_question_asks_rather_than_asserts():
    """The student is the authority on what they were thinking; that is why
    this is confirm/deny and not an automatic label."""
    q = practice.confirm_question(KNOWN["sin-cos-swap"])
    assert q.endswith("Does that match your thinking?")
    assert "?" in q


# ---------------------------------------------------------------------------
# The offline path
# ---------------------------------------------------------------------------

def test_the_mock_provider_generates_a_diagnosable_item():
    """PROVIDER=mock with the wifi off must still reach the misconception
    moment, or the offline demo stops one step short of its best beat."""
    raw = json.loads(MockProvider().complete("generate practice",
                                             json_schema=practice.GENERATE_SCHEMA))
    generated = raw["items"][0]
    known = {"velocity-implies-force": KNOWN["velocity-implies-force"]}
    assert practice.validate_item(generated, known) is None


def test_the_mock_provider_returns_hints_for_the_guardrail():
    from app.services import guardrail

    raw = json.loads(MockProvider().complete("hints please",
                                             json_schema=guardrail.HINTS_SCHEMA))
    assert raw["hints"]


def test_the_confirm_question_reads_cleanly_for_every_seeded_label():
    """All ten seeded labels are third-person descriptions. The phrasing has to
    carry each of them without needing to conjugate anything."""
    import json
    from pathlib import Path

    seed = json.loads(
        (Path(__file__).resolve().parents[1] / "data" / "seed" / "misconceptions.json")
        .read_text(encoding="utf-8"))
    for m in seed["misconceptions"]:
        q = practice.confirm_question(
            FakeMisconception(m["slug"], m["problem_type"], m["label"]))
        assert q.endswith("Does that match your thinking?")
        assert ": " in q
        assert "  " not in q
        # The label is carried verbatim apart from its first letter.
        assert m["label"][1:] in q
