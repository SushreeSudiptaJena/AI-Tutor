"""rag-003 -- answer from the material, or refuse and flag it.

The refusal is the feature. A tutor that always answers is a chatbot with a
citation field; what makes this one curriculum-aligned is that it can look at
the approved material, find that the material does not cover the question, and
say so instead of guessing.

The refusal writes a row to `uncertainty_flags`, which is the teacher
dashboard's Uncertainty Flags panel (teacher-004). One feature, two dashboards:
nothing extra has to be wired for a student's refusal to become a teacher's
to-do item.

That row carries **no user_id**, deliberately -- see `models.UncertaintyFlag`.
A teacher sees what the class could not get answered, never who asked.

Ordering matters and is not arbitrary: retrieve, then assess, then answer. The
answer call only happens once the evidence check has passed, so a question the
material cannot support never reaches an answer prompt at all -- and therefore
cannot produce prose we would have to throw away.
"""

from __future__ import annotations

from sqlalchemy.orm import Session as OrmSession

from .. import prompts
from ..models import UncertaintyFlag
from ..providers import complete
from . import evidence, retrieval

REFUSAL_BODY = (
    "I don't have approved course material covering this, so I'm not going to "
    "guess at it. I've flagged it for your teacher."
)

ANSWER_MAX_TOKENS = 1600


def ask(
    db: OrmSession,
    question: str,
    *,
    course_id: int | None,
    language: str = "en",
    topic_id: int | None = None,
    k: int = retrieval.DEFAULT_K,
) -> dict:
    """A `TutorResponse` from docs/api-contract.md.

    `outcome` is `answered` or `insufficient_evidence`. The third outcome,
    `graded_work_refused`, belongs to rag-004 and is added here later -- and
    only on `/tutor/ask`, never on a gap lesson.

    `language` is echoed as the language actually produced. Until i18n-001
    lands that is always English, and saying so is better than claiming a
    translation we did not do.
    """
    hits = retrieval.search(db, question, course_id=course_id, k=k)
    report = evidence.assess(question, hits)

    if not report.sufficient:
        flag = UncertaintyFlag(
            question=question[:2000],
            alignment_score=report.alignment_score,
            reason=report.reason or evidence.NO_MATERIAL,
            topic_id=topic_id,
            course_id=course_id,
            status="open",
        )
        db.add(flag)
        db.flush()
        return {
            "outcome": "insufficient_evidence",
            "language": "en",
            "body": REFUSAL_BODY,
            "citations": [],
            "evidence": report.to_dict(),
            "uncertainty_flag_id": flag.id,
        }

    # One call, one pair: the `[n]` the model is given is the same `n` the
    # student's citation list is numbered by.
    context, cites = retrieval.grounding(hits)

    result = complete(
        prompts.render("tutor_answer", question=question, context=context),
        max_tokens=ANSWER_MAX_TOKENS,
    )

    return {
        "outcome": "answered",
        "language": "en",
        "body": result.text.strip(),
        # Never empty on an answered response -- that is the whole point of the
        # build, and `sufficient` cannot be true with no hits.
        "citations": cites,
        "evidence": report.to_dict(),
    }
