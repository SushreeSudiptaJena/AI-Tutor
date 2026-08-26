"""rag-002 -- the syllabus alignment score, and the decision to refuse.

One object answers two questions: *how well does the approved course material
cover this?* (the percentage on every explanation card) and *is that enough to
answer at all?* (rag-003's refusal). They are the same measurement read at two
precisions, so they are computed in one place and can never disagree.

## Why this is not just top-1 similarity

Embedding similarity has a high floor. Measured on our own corpus
(`evidence/rag-002/threshold-calibration.txt`), completely unrelated text still
scores 0.39-0.54, and a question from a *nearby* field scored 0.65 against a
covered question's 0.75 -- a margin of 0.05. A judge asking something adjacent
to the syllabus is exactly the case that margin cannot survive.

So the score has two halves:

* **retrieval** -- weighted mean of the top few similarities. Rewards material
  that covers a topic in several places rather than glancing off it once.
* **entailment** -- one LLM call that reads the retrieved passages and judges
  whether they contain what the question needs. This half is load-bearing, not
  decoration: it is the only part that can tell "Newtonian mechanics" from
  "Lagrangian mechanics". Do not simplify it away. CLAUDE.md says so too.

Refusing takes **both**: similarity below the threshold, or material that does
not entail an answer, is enough to refuse on its own.

Exactly one LLM call per assessment, cached on the prompt like every other, so
a rehearsed demo question costs nothing the second time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .. import config, prompts
from ..providers import complete
from .retrieval import Hit, context_block

# Similarity weights for the top hits, best first. A second and third
# supporting passage add confidence; a fourth barely moves it.
SIMILARITY_WEIGHTS = (0.6, 0.25, 0.15)

# How the two halves combine. Retrieval is the more reliable *number*;
# entailment is the more reliable *judgement*, so it carries nearly half.
RETRIEVAL_WEIGHT = 0.55
ENTAILMENT_WEIGHT = 0.45

# Below this, the material does not answer the question even if it looks close.
ENTAILMENT_MIN = 0.5

ENTAILMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "entailment": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
    },
    "required": ["entailment", "reason"],
}

# Reasons a caller may see. Kept as constants because the teacher dashboard
# groups uncertainty flags by them.
NO_MATERIAL = "no_matching_material"
NOT_ENTAILED = "material_does_not_answer"


@dataclass(frozen=True)
class EvidenceReport:
    """The contract's `EvidenceReport`, plus the working behind it."""

    alignment_score: float
    alignment_percent: int
    top_similarity: float
    threshold: float
    sufficient: bool
    reason: str | None = None
    retrieval_score: float = 0.0
    entailment: float = 0.0
    entailment_reason: str = ""
    provider: str = ""
    cached: bool = False

    def to_dict(self) -> dict:
        """Exactly the six fields in docs/api-contract.md.

        The rest -- which provider judged it, whether it came from cache, what
        the entailment call said -- is for us, and is deliberately not part of
        the response a student's browser receives.
        """
        return {
            "alignment_score": self.alignment_score,
            "alignment_percent": self.alignment_percent,
            "top_similarity": self.top_similarity,
            "threshold": self.threshold,
            "sufficient": self.sufficient,
            "reason": self.reason,
        }


def retrieval_score(hits: list[Hit]) -> float:
    """Weighted mean of the top similarities.

    Weights are renormalised over however many hits exist, so a corpus that
    returned two passages is not penalised against one that returned three.
    """
    if not hits:
        return 0.0
    weights = SIMILARITY_WEIGHTS[: len(hits)]
    total = sum(weights)
    return sum(h.similarity * w for h, w in zip(hits, weights)) / total


def _entailment(question: str, hits: list[Hit]) -> tuple[float, str, str, bool]:
    """One LLM call: do these passages contain what the question needs?

    A malformed or failed reply must not be read as "covered" -- that would let
    a provider outage turn into a confidently wrong answer. It falls back to
    0.0, which refuses.
    """
    prompt = prompts.render(
        "evidence_entailment",
        question=question,
        context=context_block(hits),
    )
    result = complete(prompt, json_schema=ENTAILMENT_SCHEMA, max_tokens=1024)

    try:
        parsed = json.loads(result.text)
        score = float(parsed["entailment"])
        reason = str(parsed.get("reason", ""))[:300]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return 0.0, "entailment check returned an unreadable answer", result.provider, result.cached

    return max(0.0, min(1.0, score)), reason, result.provider, result.cached


def assess(
    question: str,
    hits: list[Hit],
    *,
    threshold: float | None = None,
    relaxed: bool = False,
) -> EvidenceReport:
    """Score how well the approved material covers this question.

    Pure with respect to the database: it takes the hits `retrieval.search()`
    already produced, so a caller never pays for retrieval twice and the score
    is always about the passages that were actually cited.

    `relaxed=True` is the tutor-002 second pass, run on a *wider* hit list
    after the strict one refused. It drops ONLY the similarity gate: a book
    that covers a question merely as a worked example ranks below the top-k
    similarity cut but still entails. The entailment check stays -- it is the
    half that can tell "mentioned in an example" from "near-domain miss", and
    a relaxed pass without it would answer anything embedding-adjacent. The
    report's `threshold` still shows the real configured value, so the student
    never sees a doctored number.
    """
    threshold = config.ALIGNMENT_REFUSAL_THRESHOLD if threshold is None else threshold
    top = hits[0].similarity if hits else 0.0

    if not hits:
        # No LLM call: there is nothing to entail from, and spending a provider
        # call to be told so is waste on the one path that is already a refusal.
        return EvidenceReport(
            alignment_score=0.0, alignment_percent=0, top_similarity=0.0,
            threshold=threshold, sufficient=False, reason=NO_MATERIAL,
            entailment_reason="no passages retrieved for this course",
        )

    retrieval = retrieval_score(hits)
    entail, entail_reason, provider, cached = _entailment(question, hits)
    score = RETRIEVAL_WEIGHT * retrieval + ENTAILMENT_WEIGHT * entail

    if not relaxed and top < threshold:
        reason = NO_MATERIAL
    elif entail < ENTAILMENT_MIN:
        reason = NOT_ENTAILED
    else:
        reason = None

    return EvidenceReport(
        alignment_score=round(score, 4),
        alignment_percent=round(score * 100),
        top_similarity=round(top, 4),
        threshold=threshold,
        sufficient=reason is None,
        reason=reason,
        retrieval_score=round(retrieval, 4),
        entailment=round(entail, 4),
        entailment_reason=entail_reason,
        provider=provider,
        cached=cached,
    )
