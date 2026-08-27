"""Coreference rewrite for Ask Tutor follow-ups -- tutor-003.

`/tutor/ask` is stateless by design. The transcript persists (tutor-002), but
nothing has ever been fed back into a prompt, so "explain that more simply"
was retrieved against those five literal words, failed the evidence check, and
came back as a refusal. The chat looked broken while behaving exactly as built.

This module resolves such a message into a standalone question **before**
anything else in the pipeline runs. That ordering is the whole design:

    to_english -> resolve() -> guardrail -> retrieval -> evidence -> answer

The guardrail, the retrieval query and the alignment score all measure the
question text. Give them the resolved question and they keep measuring what
they measure today -- a follow-up that resolves to a request for assignment
code is still caught by the guardrail, and the alignment badge still describes
the question the student actually meant. Stuffing raw history into the answer
prompt instead would change what all three of them score, which is exactly the
simplification `CLAUDE.md` warns against for `evidence.py`.

Three ways this stays cheap and safe:

- **No model call on the common case.** `_needs_context()` is a string test.
  A self-contained question costs nothing -- not even a database read.
- **Under-resolving is safe, over-resolving is not.** Every failure path
  returns the original question, so the worst case is today's behaviour. A
  provider outage must never become a tutor that answers the wrong question.
- **No schema change.** History is read from the existing `tutor_messages`
  rows, so nothing needs migrating on a deployed database.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from .. import prompts
from ..models import TutorMessage
from ..providers import complete

# How many previous rows to show the rewriter. Six is three exchanges, which
# covers "explain that" -> "why?" -> "and for a ManyToMany?" without the prompt
# growing every turn. This is a WINDOW, deliberately, not the whole transcript:
# a conversation that grows its own context every turn is the thing we are not
# building yet.
HISTORY_ROWS = 6

# A tutor answer is long. Only the opening matters for resolving a pronoun --
# it is where the answer says what it is about.
ANSWER_EXCERPT = 400

REWRITE_MAX_TOKENS = 300

# A rewrite fills in a missing noun. Anything dramatically longer than the
# original is the model adding subject matter the student never asked for,
# which is the one failure mode that actually changes the answer.
MAX_GROWTH_CHARS = 240

REWRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "standalone": {"type": "string"},
        "rewritten": {"type": "boolean"},
    },
    "required": ["standalone"],
}

# Words that only mean something given what came before. Matched as whole words
# so "that" fires and "thatch" does not.
_DEICTIC = re.compile(
    r"\b(that|this|these|those|it|its|they|them|their|he|she|his|her|"
    r"same|above|previous|earlier|again|instead|one)\b",
    re.IGNORECASE,
)

# Openers that are continuations rather than questions in their own right.
_CONTINUATION = re.compile(
    r"^\s*(and|but|so|or|then|also|what about|how about|why|why not|ok|okay|"
    r"go on|continue|more|simpler|explain more)\b",
    re.IGNORECASE,
)

# Below this a message cannot be self-contained whatever words it uses --
# "why?", "go on", "and then?".
SHORT_WORDS = 5


@dataclass(frozen=True)
class Resolution:
    """What the pipeline should actually ask about."""

    question: str
    rewritten: bool = False
    reason: str = ""
    original: str = ""


def _needs_context(question: str) -> bool:
    """Cheap gate, run before any database read or model call.

    Deliberately generous: a false positive costs one model call and the
    rewriter hands the question straight back, while a false negative leaves
    the student with today's unhelpful refusal. So this errs towards asking.
    """
    text = question.strip()
    if not text:
        return False
    if len(text.split()) <= SHORT_WORDS:
        return True
    return bool(_CONTINUATION.match(text) or _DEICTIC.search(text))


def _recent(db: OrmSession, user_id: int, course_id: int | None) -> list[TutorMessage]:
    """The last few turns of this student's chat, oldest first.

    Scoped to the course as well as the user: a student who switches subject
    (student-010) should not have a Django answer resolve a question they are
    now asking about C.
    """
    stmt = (
        select(TutorMessage)
        .where(TutorMessage.user_id == user_id)
        .order_by(TutorMessage.id.desc())
        .limit(HISTORY_ROWS)
    )
    if course_id is not None:
        stmt = stmt.where(TutorMessage.course_id == course_id)
    rows = list(db.execute(stmt).scalars())
    rows.reverse()
    return rows


def _transcript(rows: list[TutorMessage]) -> str:
    """Render the window as plain text for the prompt.

    A tutor row stores the whole `TutorResponse`; only its `body` says what the
    answer was about, and only the opening of that. A refusal has a body too,
    and it belongs here -- "I don't have material on this" is context a
    follow-up may well be reacting to.
    """
    lines: list[str] = []
    for row in rows:
        if row.role == "student":
            text = (row.text or "").strip()
            label = "Student"
        else:
            body = ""
            if isinstance(row.response, dict):
                body = str(row.response.get("body") or "")
            text = " ".join(body.split())[:ANSWER_EXCERPT]
            label = "Tutor"
        if text:
            lines.append(f"{label}: {text}")
    return "\n\n".join(lines)


def resolve(
    db: OrmSession,
    question: str,
    *,
    user_id: int | None,
    course_id: int | None,
) -> Resolution:
    """Turn a follow-up into a standalone question. Never raises.

    Returns the question unchanged when there is no history to resolve
    against, when the message is self-contained, or when anything at all goes
    wrong -- which keeps the stateless behaviour every existing test relies on.
    """
    original = question
    if user_id is None:
        return Resolution(question=original, reason="stateless call")

    if not _needs_context(question):
        return Resolution(question=original, reason="already self-contained")

    try:
        rows = _recent(db, user_id, course_id)
    except Exception:  # noqa: BLE001 -- a history read must never break asking
        return Resolution(question=original, reason="history unavailable")

    if not rows:
        return Resolution(question=original, reason="no prior turns")

    history = _transcript(rows)
    if not history:
        return Resolution(question=original, reason="no usable prior turns")

    try:
        result = complete(
            prompts.render("tutor_followup", history=history, question=question),
            json_schema=REWRITE_SCHEMA,
            max_tokens=REWRITE_MAX_TOKENS,
        )
        parsed = json.loads(result.text)
        standalone = str(parsed["standalone"]).strip()
    except Exception:  # noqa: BLE001 -- see the module docstring: never a new way to fail
        return Resolution(question=original, reason="rewrite unavailable")

    if not standalone:
        return Resolution(question=original, reason="rewrite was empty")

    if standalone == question.strip():
        return Resolution(question=original, reason="rewriter made no change")

    # The one failure that actually changes the answer: a rewrite that invents
    # subject matter. Length is a blunt proxy, but it is the right direction --
    # filling in a noun is short, hallucinating a topic is long.
    if len(standalone) - len(question.strip()) > MAX_GROWTH_CHARS:
        return Resolution(question=original, reason="rewrite grew too much; kept original")

    return Resolution(
        question=standalone,
        rewritten=True,
        reason="resolved against the conversation",
        original=original,
    )
