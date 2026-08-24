"""rag-004 -- decline to do graded work, without declining to teach.

The interesting part of this feature is everything it does **not** refuse.
A guardrail that refuses whenever a message resembles homework is worse than no
guardrail: it blocks the student who came to understand their homework, which
is exactly the person this tutor is for. So refusing takes **two** independent
signals, and both must fire:

  1. the message matches graded material by vector similarity (> 0.80), and
  2. an intent check says the student wants the *deliverable* rather than the
     *understanding*.

Order is not an implementation detail. The vector match is cheap and local; the
intent check costs a model call and a second of latency. Running the cheap one
first means the expensive one only happens on the small fraction of messages
that look like homework at all -- most questions never pay for it.

The asymmetry is deliberate too. A false refusal blocks a student who came to
learn and gives them no way to appeal; a false answer means someone who wanted
the answer got an explanation instead. Those are not equally bad, so ties go to
answering: unclear intent, low confidence, or a failed intent call all answer.

Scope: **`/tutor/ask` only.** Never gap lessons, never practice. Those are
driven by a concept or a generated item rather than by text the student typed,
so there is no request-for-the-solution to detect and a refusal could only ever
be a false positive. See CLAUDE.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session as OrmSession

from .. import prompts
from ..providers import complete
from . import retrieval

# Above this, the message is close enough to graded material to be worth an
# intent call. Deliberately high: this gate exists to keep the LLM call rare,
# not to make the refusal decision, which the intent check makes.
ASSIGNMENT_SIMILARITY = 0.80

# Below this the model is guessing, and a guess should not refuse a student.
MIN_INTENT_CONFIDENCE = 0.6

MAX_HINTS = 5

INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["solve", "understand"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
    },
    "required": ["intent", "confidence"],
}

HINTS_SCHEMA = {
    "type": "object",
    "properties": {
        "hints": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["hints"],
}


@dataclass(frozen=True)
class Verdict:
    """Why the guardrail did or did not fire. Every field is here so a refusal
    can be explained to a teacher who thinks it was wrong."""

    refuse: bool
    similarity: float
    material_id: int | None = None
    material_title: str = ""
    assignment_text: str = ""
    intent: str = ""
    confidence: float = 0.0
    reason: str = ""

    @property
    def matched_assignment(self) -> dict | None:
        if self.material_id is None:
            return None
        return {"material_id": self.material_id, "title": self.material_title}


def _intent(question: str, assignment_text: str) -> tuple[str, float, str]:
    """One model call: deliverable, or understanding?

    A malformed or failed reply resolves to `understand`. The alternative --
    treating a provider hiccup as grounds to refuse -- would turn an outage into
    a tutor that stonewalls students, which is the worst failure this system
    has.
    """
    result = complete(
        prompts.render("guardrail_intent", question=question,
                       assignment=" ".join(assignment_text.split())[:1500]),
        json_schema=INTENT_SCHEMA,
        max_tokens=1024,
    )
    try:
        parsed = json.loads(result.text)
        intent = str(parsed["intent"]).strip().lower()
        confidence = float(parsed.get("confidence", 0.0))
        reason = str(parsed.get("reason", ""))[:300]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return "understand", 0.0, "intent check returned an unreadable answer"

    if intent not in ("solve", "understand"):
        return "understand", 0.0, f"intent check returned {intent!r}"
    return intent, max(0.0, min(1.0, confidence)), reason


def check(db: OrmSession, question: str, *, course_id: int | None) -> Verdict:
    """Should this message be refused as graded work?

    Cheap first: if nothing in the assignment corpus is close, this costs one
    vector search and returns.
    """
    hits = retrieval.search_assignments(db, question, course_id=course_id, k=1)
    if not hits:
        return Verdict(refuse=False, similarity=0.0, reason="no assignment material")

    top = hits[0]
    if top.similarity <= ASSIGNMENT_SIMILARITY:
        return Verdict(
            refuse=False,
            similarity=round(top.similarity, 4),
            reason="does not match graded material closely enough",
        )

    intent, confidence, reason = _intent(question, top.text)
    refuse = intent == "solve" and confidence >= MIN_INTENT_CONFIDENCE

    return Verdict(
        refuse=refuse,
        similarity=round(top.similarity, 4),
        material_id=top.material_id,
        material_title=top.book_title,
        assignment_text=top.text,
        intent=intent,
        confidence=round(confidence, 3),
        reason=reason or ("asking for the solution" if refuse else "asking to understand"),
    )


def hints(question: str, hits: list[retrieval.Hit]) -> list[str]:
    """Scaffolded steps to hand back with the refusal.

    A bare "I won't do your homework" teaches nothing and sends the student to
    a chatbot that will. Refusing is only defensible if the refusal still helps.
    """
    context, _ = retrieval.grounding(hits)
    result = complete(
        prompts.render("guardrail_hints", question=question, context=context),
        json_schema=HINTS_SCHEMA,
        max_tokens=1024,
    )
    try:
        parsed = json.loads(result.text)
        out = [str(h).strip() for h in parsed["hints"] if str(h).strip()]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return []
    return out[:MAX_HINTS]
