"""teacher-006 -- draft a reteach unit against one shared misconception.

The human-in-the-loop feature. Everything here produces a **draft**, and a
draft reaches no student. Approval is a separate, deliberate act by a teacher,
and it is the only thing that changes that.

That gate is the point, not a formality. The system is willing to say "14 of
your students believe X" and to write the lesson that argues against X -- but
the claim that a class holds a misconception is a claim about people, made by a
model, and a teacher is the only one who can look at it and know whether it is
true of their room. Auto-assigning would turn a good suggestion into an
unreviewed instruction.

Drafting refuses when the corpus cannot support it. A reteach unit that the
approved material does not back is invented content wearing a teacher's name
once approved, which is exactly what "curriculum-aligned" is supposed to rule
out. See `assess()` in evidence.py -- the same gate the student side uses.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session as OrmSession

from .. import prompts
from ..models import Misconception, Topic
from ..providers import complete
from . import evidence, retrieval

DRAFT_MAX_TOKENS = 1400

RETEACH_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"},
    },
    "required": ["title", "body"],
}


class NotSupported(RuntimeError):
    """The approved corpus cannot support a unit on this misconception."""

    def __init__(self, report):
        super().__init__("insufficient evidence for a reteach unit")
        self.report = report


def draft(db: OrmSession, misconception: Misconception, *, k: int = retrieval.DEFAULT_K):
    """Return `(title, body, citations, report)` for a proposed unit.

    The retrieval query is built from the misconception's label and
    description rather than from its topic name. "Puts the foreign key on the
    one side of a one-to-many relationship" retrieves the passage about which
    side carries the key; "Relational data" retrieves the chapter opener. The
    unit is about the specific error, so the search should be too.
    """
    course_id = None
    if misconception.topic_id is not None:
        topic = db.get(Topic, misconception.topic_id)
        course_id = topic.course_id if topic else None

    query = f"{misconception.label}. {misconception.description or ''}".strip()
    hits = retrieval.search(db, query, course_id=course_id, k=k)
    report = evidence.assess(query, hits)
    if not report.sufficient:
        raise NotSupported(report)

    context, cites = retrieval.grounding(hits)
    result = complete(
        prompts.render("reteach_suggest",
                       label=misconception.label,
                       description=misconception.description or "",
                       context=context),
        json_schema=RETEACH_SCHEMA,
        max_tokens=DRAFT_MAX_TOKENS,
    )

    title, body = "", ""
    try:
        parsed = json.loads(result.text)
        title = str(parsed.get("title", "")).strip()
        body = str(parsed.get("body", "")).strip()
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # A draft with no body is worse than no draft: it looks like the feature
    # ran and produced nothing worth reading. Fall back to something the
    # teacher can edit rather than to an empty box.
    if not title:
        title = f"Reteach: {misconception.label}"[:300]
    if not body:
        body = (
            f"{misconception.description or misconception.label}\n\n"
            "The model did not return a usable draft. The citations below are "
            "the approved material this unit should be built from."
        )

    return title[:300], body, cites, report
