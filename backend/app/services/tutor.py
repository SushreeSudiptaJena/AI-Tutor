"""rag-003 -- answer from the material, or refuse and flag it.
tutor-002 -- and when refusing, try harder before leaving the student stuck.

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
material cannot support never reaches an answer prompt as if it were grounded.

tutor-002 changed what happens *after* a strict refusal, in two steps:

1. **Wide retry.** The strict pass ranks the top-k passages and refuses if the
   best is below threshold. A book that covers a question only implicitly --
   a worked example, a passing mention -- ranks below that cut while still
   being real coverage. The retry searches wider and re-assesses with the
   similarity gate dropped (`evidence.assess(relaxed=True)`); the entailment
   check still has to pass. A retry that passes is answered like any other
   question, with real citations, and writes NO flag -- the material did
   cover it; the first pass simply looked too narrowly.
2. **General-knowledge fallback.** If the retry also fails, the refusal stands
   -- outcome, empty citations, evidence report and teacher flag all exactly
   as before -- but the response now carries a `beyond_syllabus` block: a real
   answer from the model's own knowledge, rendered under a warning, with no
   citations and no alignment badge. The student is helped AND told the truth
   about where the help came from. A provider failure in this last step
   degrades to the plain rag-003 refusal rather than erroring.
"""

from __future__ import annotations

from sqlalchemy.orm import Session as OrmSession

from .. import prompts
from ..models import TutorMessage, UncertaintyFlag
from ..providers import complete
from . import evidence, guardrail, language as lang, retrieval, speech

REFUSAL_BODY = (
    "I don't have approved course material covering this, so I won't cite any "
    "of it. I've flagged the question for your teacher -- and below is what I "
    "can offer from general knowledge, clearly marked as such."
)

GRADED_WORK_BODY = (
    "This looks like it's from a graded assignment, so I'm not going to solve "
    "it for you. Here's how to approach it yourself."
)

BEYOND_NOTE = (
    "Not checked against your course material — general knowledge. "
    "Verify with your teacher."
)

ANSWER_MAX_TOKENS = 1600

# tutor-002 wide retry. Twice the default window, so a concept that the book
# demonstrates in an example buried mid-chapter gets a second chance to be
# found before the tutor steps outside the syllabus.
WIDE_K = retrieval.DEFAULT_K * 2 + 2


def ask(
    db: OrmSession,
    question: str,
    *,
    course_id: int | None,
    language: str = "en",
    topic_id: int | None = None,
    k: int = retrieval.DEFAULT_K,
    user_id: int | None = None,
) -> dict:
    """A `TutorResponse` from docs/api-contract.md.

    `outcome` is `answered`, `insufficient_evidence`, or `graded_work_refused`.
    The third is reachable **only from here** -- `lesson()` below never returns
    it, because a gap lesson is concept-driven and a refusal there could only be
    a false positive. It also never gains the `beyond_syllabus` fallback: the
    guardrail refuses, it does not help around itself.

    `language` is echoed as the language actually produced -- not as the
    language that was requested. Translation can fail silently (see
    `services/language.py`), and labelling English prose `hi` would tell the
    student the system answered in their language when it did not.

    `user_id` (from the router, never the request body) turns on tutor-002
    persistence: the question as typed and the full response are written to
    `tutor_messages` so GET /tutor/history can rebuild the chat. Without it the
    call is stateless, exactly as it was -- which is what the unit tests rely
    on.
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
        out = {
            "outcome": "graded_work_refused",
            "language": produced,
            "body": body,
            "speech_text": speech.for_speech(body),
            # The hints are the useful half of a refusal. Translating the
            # sentence that says "no" and leaving the help in English would be
            # the worst of both.
            "hints": [lang.from_english(h, target)[0] for h in hints],
            "citations": cites,
            "matched_assignment": verdict.matched_assignment,
        }
        _remember(db, user_id, course_id, question, out)
        return out

    report = evidence.assess(asked_in_english, hits)

    if not report.sufficient and hits:
        # tutor-002, step 1: the strict window may simply have been too narrow.
        # A wider search assessed with the similarity gate dropped (but the
        # entailment check intact) finds coverage the book provides only as an
        # example. One extra vector query and at most one extra LLM call, paid
        # only on the refusal path.
        wide = retrieval.search(db, asked_in_english, course_id=course_id, k=WIDE_K)
        retry = evidence.assess(asked_in_english, wide, relaxed=True)
        if retry.sufficient:
            report = retry
            hits = wide

    if report.sufficient:
        # Reached either directly (strict pass) or through the wide retry. A
        # retry rescue writes NO uncertainty flag: the approved material did
        # cover the question, so there is nothing for the teacher to fix.
        # One call, one pair: the `[n]` the model is given is the same `n` the
        # student's citation list is numbered by.
        context, cites = retrieval.grounding(hits)

        result = complete(
            prompts.render("tutor_answer", question=asked_in_english, context=context),
            max_tokens=ANSWER_MAX_TOKENS,
        )

        # Translated LAST, after the evidence check has already scored the
        # English text. `citations` and `evidence` are deliberately untouched:
        # the citation names a real English page, and the score is a property
        # of the answer, not of the language it is read in.
        body, produced = lang.from_english(result.text.strip(), target)

        out = {
            "outcome": "answered",
            "language": produced,
            "body": body,
            # a11y-001. The same answer with the markdown taken out, because
            # read-aloud points at this response and "[4]" is spoken as "four".
            "speech_text": speech.for_speech(body),
            # Never empty on an answered response -- that is the whole point of
            # the build, and `sufficient` cannot be true with no hits.
            "citations": cites,
            "evidence": report.to_dict(),
        }
        _remember(db, user_id, course_id, question, out)
        return out

    # The refusal itself, from here on, is unchanged rag-003. The flag stores
    # the ENGLISH question. A teacher reading the uncertainty panel should not
    # need the student's language to know what was asked, and the panel is one
    # list mixing every language.
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
    out = {
        "outcome": "insufficient_evidence",
        "language": produced,
        "body": body,
        "speech_text": speech.for_speech(body),
        "citations": [],
        "evidence": report.to_dict(),
        "uncertainty_flag_id": flag.id,
    }

    # tutor-002, step 2: the refusal stands, but the student is not left at a
    # dead end. One more model call, no citations, and a note the UI renders
    # as a warning. A provider failure here degrades to the plain rag-003
    # refusal -- this is help bolted onto a refusal, never a new way to fail.
    try:
        general = complete(
            prompts.render("tutor_general", question=asked_in_english),
            max_tokens=ANSWER_MAX_TOKENS,
        )
        g_body, _ = lang.from_english(general.text.strip(), target)
        g_note, _ = lang.from_english(BEYOND_NOTE, target)
        out["beyond_syllabus"] = {"body": g_body, "note": g_note}
    except Exception:  # noqa: BLE001 -- the refusal is complete and correct without this
        pass

    _remember(db, user_id, course_id, question, out)
    return out


def _remember(
    db: OrmSession,
    user_id: int | None,
    course_id: int | None,
    question: str,
    response: dict,
) -> None:
    """Write the chat turn -- tutor-002. No user_id, no persistence."""
    if user_id is None:
        return
    db.add(TutorMessage(user_id=user_id, course_id=course_id, role="student", text=question))
    db.add(TutorMessage(user_id=user_id, course_id=course_id, role="tutor", response=response))


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
