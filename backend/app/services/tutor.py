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
from . import evidence, guardrail, language as lang, retrieval, speech

REFUSAL_BODY = (
    "I don't have approved course material covering this, so I'm not going to "
    "guess at it. I've flagged it for your teacher."
)

GRADED_WORK_BODY = (
    "This looks like it's from a graded assignment, so I'm not going to solve "
    "it for you. Here's how to approach it yourself."
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

    `outcome` is `answered`, `insufficient_evidence`, or `graded_work_refused`.
    The third is reachable **only from here** -- `lesson()` below never returns
    it, because a gap lesson is concept-driven and a refusal there could only be
    a false positive.

    `language` is echoed as the language actually produced -- not as the
    language that was requested. Translation can fail silently (see
    `services/language.py`), and labelling English prose `hi` would tell the
    student the system answered in their language when it did not.
    """
    # i18n-001. Everything from here to the return is English: the corpus is
    # English, the embeddings are English, and the guardrail's vector match and
    # the evidence check both have to happen in the same space as the material
    # they compare against. Translating at the edges rather than in the middle
    # is what keeps the alignment score identical across languages.
    target = lang.normalise(language)
    asked_in_english = lang.to_english(question, target)

    # The guardrail runs before retrieval so a request to do graded work never
    # reaches an answer prompt. Its first gate is a vector search, so the
    # common case -- a question that is not homework at all -- costs one query
    # and no model call.
    verdict = guardrail.check(db, asked_in_english, course_id=course_id)

    hits = retrieval.search(db, asked_in_english, course_id=course_id, k=k)

    if verdict.refuse:
        # Hints are grounded in the same approved material a lesson would use,
        # so a refusal still points somewhere real.
        _, cites = retrieval.grounding(hits)
        hints = guardrail.hints(asked_in_english, hits)
        body, produced = lang.from_english(GRADED_WORK_BODY, target)
        # The hints are the useful half of a refusal. Translating the sentence
        # that says "no" and leaving the help in English would be the worst of
        # both.
        return {
            "outcome": "graded_work_refused",
            "language": produced,
            "body": body,
            "speech_text": speech.for_speech(body),
            "hints": [lang.from_english(h, target)[0] for h in hints],
            "citations": cites,
            "matched_assignment": verdict.matched_assignment,
        }

    report = evidence.assess(asked_in_english, hits)

    if not report.sufficient:
        # The flag stores the ENGLISH question. A teacher reading the
        # uncertainty panel should not need the student's language to know
        # what was asked, and the panel is one list mixing every language.
        flag = UncertaintyFlag(
            question=asked_in_english[:2000],
            alignment_score=report.alignment_score,
            reason=report.reason or evidence.NO_MATERIAL,
            topic_id=topic_id,
            course_id=course_id,
            status="open",
        )
        db.add(flag)
        db.flush()
        body, produced = lang.from_english(REFUSAL_BODY, target)
        return {
            "outcome": "insufficient_evidence",
            "language": produced,
            "body": body,
            "speech_text": speech.for_speech(body),
            "citations": [],
            "evidence": report.to_dict(),
            "uncertainty_flag_id": flag.id,
        }

    # One call, one pair: the `[n]` the model is given is the same `n` the
    # student's citation list is numbered by.
    context, cites = retrieval.grounding(hits)

    result = complete(
        prompts.render("tutor_answer", question=asked_in_english, context=context),
        max_tokens=ANSWER_MAX_TOKENS,
    )

    # Translated LAST, after the evidence check has already scored the English
    # text. `citations` and `evidence` are deliberately untouched: the citation
    # names a real English page, and the score is a property of the answer, not
    # of the language it is read in.
    body, produced = lang.from_english(result.text.strip(), target)

    return {
        "outcome": "answered",
        "language": produced,
        "body": body,
        # a11y-001. The same answer with the markdown taken out, because
        # read-aloud points at this response and "[4]" is spoken as "four".
        "speech_text": speech.for_speech(body),
        # Never empty on an answered response -- that is the whole point of the
        # build, and `sufficient` cannot be true with no hits.
        "citations": cites,
        "evidence": report.to_dict(),
    }


def lesson(
    db: OrmSession,
    concept_name: str,
    *,
    course_id: int | None,
    topic_name: str | None = None,
    language: str = "en",
    k: int = retrieval.DEFAULT_K,
) -> dict:
    """A `TutorResponse` teaching one concept from the approved material.

    Concept-driven, not text-driven: the student never typed anything, they
    clicked a gap. That is exactly why the graded-work guardrail must never run
    here -- there is no "asking for the solution" to detect, so any refusal
    would be a false positive on a student trying to learn. See rag-004 in
    CLAUDE.md.

    A lesson can still come back `insufficient_evidence`, and should: if the
    approved corpus does not cover a prerequisite the diagnostic tests for, the
    honest answer is to say so and flag it, not to improvise a lesson. That
    combination -- we test it but we cannot teach it -- is precisely what a
    teacher needs to see in the uncertainty panel.
    """
    # The concept name comes from the database, which is English, so nothing
    # needs translating on the way IN here -- unlike ask(), where the student
    # typed the question. Only the way out.
    target = lang.normalise(language)

    query = f"Explain {concept_name}"
    if topic_name:
        query += f" in {topic_name}"

    hits = retrieval.search(db, query, course_id=course_id, k=k)
    report = evidence.assess(query, hits)

    if not report.sufficient:
        flag = UncertaintyFlag(
            question=f"[gap lesson] {concept_name}",
            alignment_score=report.alignment_score,
            reason=report.reason or evidence.NO_MATERIAL,
            course_id=course_id,
            status="open",
        )
        db.add(flag)
        db.flush()
        body, produced = lang.from_english(
            f"I don't have approved course material covering {concept_name} "
            f"well enough to teach it. I've flagged it for your teacher.",
            target,
        )
        return {
            "outcome": "insufficient_evidence",
            "language": produced,
            "body": body,
            "speech_text": speech.for_speech(body),
            "citations": [],
            "evidence": report.to_dict(),
            "uncertainty_flag_id": flag.id,
        }

    context, cites = retrieval.grounding(hits)
    result = complete(
        prompts.render("gap_lesson", concept=concept_name, context=context),
        max_tokens=ANSWER_MAX_TOKENS,
    )
    # Same boundary as ask(): scored in English, then translated. The alignment
    # badge on a Hindi lesson card is the number the English lesson scored.
    body, produced = lang.from_english(result.text.strip(), target)
    return {
        "outcome": "answered",
        "language": produced,
        "body": body,
        "speech_text": speech.for_speech(body),
        "citations": cites,
        "evidence": report.to_dict(),
    }
