"""student-005 / student-006 -- scoped practice, and the misconception behind a
wrong answer.

## Why generated items declare their own distractors

A wrong answer is only diagnosable if something knows *which mistake produces
it*. The seeded items carry that knowledge as a regex per misconception --
`sin-cos-swap` matches `^5(\\.0+)?\\s*N$`, because the seeded question is 10 N
at 30 degrees and a student who swaps sine for cosine lands on exactly 5 N.

Those regexes are welded to the seeded numbers. A generated question about 14 N
at 40 degrees produces a different wrong value, matches nothing, and yields no
diagnosis -- and the failure is silent. The student just sees a wrong answer
with no explanation of their reasoning, which is the single most important
moment in the demo quietly not happening.

So the generator is required to say, per item, which misconception each
distractor was built from. That mapping is stored on the item and read back at
answer time, and it is exact rather than inferred.

It lives inside the `options` JSON column, alongside `choices`, which is
precisely why that column is a dict rather than a list. The API's
`_options_list()` unwraps `choices` only, so the mapping cannot leak to a
client -- it would be an answer key.

## Falling back

Generation is validated, retried once, and then falls back to the seeded items
for the concept. A generated item that no misconception maps onto is worse than
a seeded one that does, because the seeded ones are the demo.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from .. import prompts
from ..models import (
    Concept,
    Misconception,
    PracticeItem,
    PracticeSet,
)
from ..providers import complete
from . import retrieval

DEFAULT_COUNT = 4
MAX_COUNT = 8
GENERATE_ATTEMPTS = 2
OPTIONS_PER_ITEM = 4

GENERATE_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "kind": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "correct_answer": {"type": "string"},
                    "problem_type": {"type": "string"},
                    "distractors": {"type": "object"},
                },
                "required": ["prompt", "options", "correct_answer",
                             "problem_type", "distractors"],
            },
        }
    },
    "required": ["items"],
}

EXPLAIN_MAX_TOKENS = 900


# ---------------------------------------------------------------------------
# Which misconceptions belong to a concept
# ---------------------------------------------------------------------------

def misconceptions_for_concept(db: OrmSession, concept: Concept) -> list[Misconception]:
    """The misconceptions a question on this concept could plausibly trigger.

    Preferred link is `problem_type`: the seeded practice items already say
    which problem types belong to which concept, and a misconception is only
    ever matched against an item of the same type. Falling back to the whole
    topic is deliberately second choice -- a topic holds several concepts, and
    offering the generator a misconception from a neighbouring one invites an
    item that is not about this gap at all.
    """
    types = [
        row[0] for row in db.execute(
            select(PracticeItem.problem_type)
            .where(PracticeItem.concept_id == concept.id)
            .group_by(PracticeItem.problem_type)
        ).all()
    ]
    if types:
        rows = db.scalars(
            select(Misconception).where(Misconception.problem_type.in_(types))
        ).all()
        if rows:
            return list(rows)

    return list(db.scalars(
        select(Misconception).where(Misconception.topic_id == concept.topic_id)
    ).all())


def _misconception_block(misconceptions: list[Misconception]) -> str:
    parts = []
    for m in misconceptions:
        parts.append(
            f"- slug: {m.slug}\n"
            f"  problem_type: {m.problem_type}\n"
            f"  mistake: {m.label}\n"
            f"  reasoning: {' '.join((m.description or '').split())[:300]}"
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Validation -- a generated item that cannot be diagnosed is not usable
# ---------------------------------------------------------------------------

@dataclass
class Rejected:
    index: int
    reason: str


def validate_item(raw: dict, known: dict[str, Misconception]) -> str | None:
    """Return why this item is unusable, or None if it is fine."""
    options = raw.get("options") or []
    if len(options) != OPTIONS_PER_ITEM:
        return f"expected {OPTIONS_PER_ITEM} options, got {len(options)}"
    if len(set(options)) != len(options):
        return "duplicate options"
    if not str(raw.get("prompt", "")).strip():
        return "empty prompt"

    correct = raw.get("correct_answer")
    if correct not in options:
        return "correct_answer is not one of the options"

    problem_type = raw.get("problem_type")
    if not any(m.problem_type == problem_type for m in known.values()):
        return f"unknown problem_type {problem_type!r}"

    distractors = raw.get("distractors") or {}
    if not isinstance(distractors, dict):
        return "distractors is not an object"

    usable = {
        option: slug for option, slug in distractors.items()
        if option in options and option != correct and slug in known
    }
    if not usable:
        # The whole point of the feature. An item with no diagnosable wrong
        # answer produces the demo's weakest moment: a wrong answer, and
        # silence.
        return "no wrong option maps to a known misconception"
    return None


def _clean_distractors(raw: dict, known: dict[str, Misconception]) -> dict[str, str]:
    correct = raw.get("correct_answer")
    return {
        option: slug
        for option, slug in (raw.get("distractors") or {}).items()
        if option in raw["options"] and option != correct and slug in known
    }


# ---------------------------------------------------------------------------
# student-005 -- generate
# ---------------------------------------------------------------------------

def _generate_raw(concept: Concept, misconceptions: list[Misconception],
                  context: str, count: int) -> list[dict]:
    prompt = prompts.render(
        "practice_generate",
        concept=f"{concept.name} (write {count} questions)",
        misconceptions=_misconception_block(misconceptions),
        context=context,
    )
    result = complete(prompt, json_schema=GENERATE_SCHEMA, max_tokens=2048)
    try:
        parsed = json.loads(result.text)
        items = parsed["items"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []
    return items if isinstance(items, list) else []


def seeded_items_for_concept(db: OrmSession, concept: Concept) -> list[PracticeItem]:
    return list(db.scalars(
        select(PracticeItem)
        .where(PracticeItem.concept_id == concept.id, PracticeItem.is_seed.is_(True))
        .order_by(PracticeItem.id)
    ).all())


def generate(
    db: OrmSession,
    *,
    user_id: int,
    concept: Concept,
    course_id: int | None,
    gap_id: int | None = None,
    count: int = DEFAULT_COUNT,
) -> tuple[PracticeSet, list[PracticeItem], list[Rejected], bool]:
    """Build a practice set for one gap.

    Returns the set, its items, whatever was rejected and why, and whether the
    seeded fallback was used. The rejections are returned rather than swallowed
    so a failing generator shows up in the response we can look at, instead of
    as a quietly shorter list of questions.
    """
    count = max(1, min(count, MAX_COUNT))
    known = {m.slug: m for m in misconceptions_for_concept(db, concept)}

    practice_set = PracticeSet(user_id=user_id, gap_id=gap_id)
    db.add(practice_set)
    db.flush()

    accepted: list[dict] = []
    rejected: list[Rejected] = []

    if known:
        hits = retrieval.search(db, f"{concept.name} worked examples",
                                course_id=course_id, k=retrieval.DEFAULT_K)
        context, _ = retrieval.grounding(hits)
        misc_list = list(known.values())

        for attempt in range(GENERATE_ATTEMPTS):
            for index, raw in enumerate(_generate_raw(concept, misc_list, context, count)):
                if len(accepted) >= count:
                    break
                problem = validate_item(raw, known)
                if problem:
                    rejected.append(Rejected(index=index, reason=problem))
                    continue
                accepted.append(raw)
            if accepted:
                break

    used_fallback = False
    items: list[PracticeItem] = []

    if accepted:
        for raw in accepted:
            item = PracticeItem(
                practice_set_id=practice_set.id,
                concept_id=concept.id,
                problem_type=raw["problem_type"],
                prompt=raw["prompt"].strip(),
                kind="mcq",
                options={
                    "choices": list(raw["options"]),
                    # Never serialised to a client -- see _options_list().
                    "distractors": _clean_distractors(raw, known),
                },
                correct_answer=str(raw["correct_answer"]),
                is_seed=False,
            )
            db.add(item)
            items.append(item)
    else:
        # Demo insurance. A seeded item that diagnoses beats a generated one
        # that does not.
        used_fallback = True
        for seed in seeded_items_for_concept(db, concept)[:count]:
            item = PracticeItem(
                practice_set_id=practice_set.id,
                concept_id=concept.id,
                problem_type=seed.problem_type,
                prompt=seed.prompt,
                kind=seed.kind,
                options=dict(seed.options or {}),
                correct_answer=seed.correct_answer,
                is_seed=True,
            )
            db.add(item)
            items.append(item)

    db.flush()
    return practice_set, items, rejected, used_fallback


# ---------------------------------------------------------------------------
# student-006 -- diagnose
# ---------------------------------------------------------------------------

def is_correct(given: str, expected: str) -> bool:
    return " ".join(str(given).split()).lower() == " ".join(str(expected).split()).lower()


def diagnose(db: OrmSession, item: PracticeItem, answer: str) -> tuple[Misconception | None, str]:
    """Which misconception produced this wrong answer?

    Declared mapping first: for a generated item the generator already said
    which mistake it built each distractor from, and that is exact.

    The seeded regexes are the fallback, and they only apply within the same
    `problem_type` -- matching across types is what turns a specific diagnosis
    into a generic one, and a generic diagnosis is worse than none because the
    student is asked to confirm reasoning that was never theirs.
    """
    declared = (item.options or {}).get("distractors") or {}
    slug = declared.get(answer) or declared.get(answer.strip())
    if slug:
        found = db.scalar(select(Misconception).where(Misconception.slug == slug))
        if found is not None:
            return found, "pattern"

    candidates = db.scalars(
        select(Misconception).where(Misconception.problem_type == item.problem_type)
    ).all()
    for m in candidates:
        if not m.wrong_answer_pattern:
            continue
        try:
            if re.search(m.wrong_answer_pattern, answer):
                return m, "pattern"
        except re.error:
            continue

    return None, "none"


def confirm_question(misconception: Misconception) -> str:
    """What the student is asked to agree or disagree with.

    Phrased as a question about *their* reasoning, not as a verdict. The
    student is the authority on what they were thinking, which is the whole
    reason this is confirm/deny rather than an automatic label.
    """
    label = misconception.label
    label = label[0].lower() + label[1:] if label else "that reasoning"
    # Built by template rather than by a model call. This line is on screen at
    # the most important moment of the demo, so it must read the same way every
    # time -- and the ten seeded labels are all third-person descriptions
    # ("treats constant velocity as..."), which this phrasing carries cleanly
    # without needing to conjugate them into second person.
    return (f"That answer usually comes from this reasoning: {label}. "
            f"Does that match your thinking?")


def explain(db: OrmSession, item: PracticeItem, answer: str, correct: bool,
            course_id: int | None) -> tuple[str, list[dict]]:
    """A grounded explanation of the item, with citations."""
    hits = retrieval.search(db, item.prompt, course_id=course_id, k=3)
    context, cites = retrieval.grounding(hits)
    if not hits:
        return "", []

    result = complete(
        prompts.render(
            "practice_explain",
            question=item.prompt,
            correct_answer=item.correct_answer,
            given_answer=answer if not correct else "(they answered correctly)",
            context=context,
        ),
        max_tokens=EXPLAIN_MAX_TOKENS,
    )
    return result.text.strip(), cites
