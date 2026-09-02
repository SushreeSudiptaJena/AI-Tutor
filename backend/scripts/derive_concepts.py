"""concept-001 -- read a course's syllabus out of the corpus it was ingested from.

    .venv/Scripts/python.exe backend/scripts/derive_concepts.py --course CSW2 --material 12
    ... --dry-run          derive and print, write nothing
    ... --windows 20       stop after N windows (a bounded first pass)
    ... --window-size 8    chunks per model call
    ... --report           print what has already been derived, and exit

Concepts used to come from exactly one place: a human writing
`backend/data/seed/concepts.json`. Fifteen of them, for a 1,190-page book. This
script is the other half -- it reads the book and says what is in it.

HOW IT GROUPS
-------------
A **sliding window of consecutive chunks within one chapter**, in page order.
Not embedding clusters, and the difference matters: a cluster of semantically
similar passages is scattered across the whole book, so the concept it produces
cannot say which pages teach it. A contiguous window can, and page anchoring is
the thing every citation in this project rests on. Every derived concept comes
out with a real `(material_id, page_start, page_end)`.

Chapters become topics. The Django book has 21 of them and they are already on
every chunk, so the topic layer is free and is the book's own structure rather
than one invented for it.

WHY DEDUPLICATION IS NOT OPTIONAL
---------------------------------
Adjacent windows overlap in subject matter -- a chapter spends thirty pages on
one idea. Without a merge step the same concept arrives four times under four
slightly different names, and a syllabus with four "URL routing" lines is worse
than no syllabus.

**The merge cannot be a similarity threshold, and that is measured, not
assumed.** See the comment on MERGE_CANDIDATE: restatements of one concept and
genuinely different concepts occupy OVERLAPPING similarity bands, so any single
cut-off either keeps duplicates or destroys real syllabus lines. Similarity is
the cheap first gate and a model call decides -- the same two-stage shape the
evidence check already uses for exactly the same reason.

A merge WIDENS the kept concept's page range rather than discarding the second
sighting. That is the useful half of the duplicate: it is evidence the concept
spans more pages than the first window showed. A merge into a SEEDED concept
never touches that row -- a human wrote it on purpose.

COST
----
One model call per window. The Django book is 1,938 chunks, so ~242 calls at
the default window size. Every one goes through the disk cache, so a second run
over the same book is free and offline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.orm import Session as OrmSession  # noqa: E402

from app import prompts  # noqa: E402
from app.db import get_sessionmaker  # noqa: E402
from app.models import (  # noqa: E402
    Chunk,
    Concept,
    Course,
    DiagnosticItem,
    Material,
    Topic,
)
from app.providers import AllProvidersFailed, complete  # noqa: E402
from app.services import embed  # noqa: E402

# SIMILARITY ALONE CANNOT DECIDE THIS, AND THAT IS MEASURED.
#
# On the first 11 names derived from the Django book, restatements of ONE
# concept scored 0.7829-0.8625 and genuinely different concepts 0.4757-0.7970.
# THE BANDS OVERLAP: "Django project file structure" vs "Django project
# settings" is 0.7970, higher than the 0.7829 between two real restatements of
# the virtual-environments concept. No threshold merges the duplicates without
# also merging two different concepts. Full working:
# evidence/concept-001/dedupe-calibration.txt
#
# So this is the same shape as ALIGNMENT_REFUSAL_THRESHOLD and gets the answer
# this repo already settled on there: similarity is a cheap FIRST gate and a
# model call decides. The gate sits BELOW the floor of true restatements, so it
# never gates a duplicate out -- it only decides how often the decider runs
# (6 of 55 pairs in the calibration).
MERGE_CANDIDATE = 0.75

# How many near neighbours to put in front of the decider at once. One call per
# new concept, not one per pair.
MAX_CANDIDATES = 5

# A window has to be big enough to contain a whole idea and small enough that
# the model does not summarise the chapter. 8 chunks is roughly 4-6 book pages.
DEFAULT_WINDOW = 8

# Front matter reads exactly like a syllabus and is not one. The first dry run
# over the Django book "derived" Django overview / Django architecture /
# Request-response cycle from pages 9-15 -- which is its TABLE OF CONTENTS. A
# contents page is a list of concept names with no teaching behind any of them,
# so every concept it yields is one whose lesson would immediately refuse.
# Chunks with no chapter label at all are front matter for the same reason:
# the ingester assigns a chapter once the first chapter heading appears.
SKIP_CHAPTERS = re.compile(
    r"^\s*(preface|foreword|contents|table of contents|index|about the "
    r"(author|reviewer)s?|acknowledge?ments|copyright|dedication|colophon|"
    r"packt|\(front matter\))",
    re.I,
)

DERIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "summary": {"type": "string"},
                    "prerequisite": {"type": "boolean"},
                },
                "required": ["name", "summary", "prerequisite"],
            },
        }
    },
    "required": ["concepts"],
}

SAME_SCHEMA = {
    "type": "object",
    "properties": {"duplicate_of": {"type": ["string", "null"]}},
    "required": ["duplicate_of"],
}

ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "skip": {"type": "boolean"},
        "prompt": {"type": "string"},
        "options": {"type": "array", "items": {"type": "string"}},
        "correct_answer": {"type": "string"},
    },
}


def log(msg: str = "") -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# slugs
# ---------------------------------------------------------------------------

def slugify(text: str, *, maxlen: int = 80) -> str:
    """ASCII, lowercase, hyphenated. `Concept.slug` is unique and 80 chars."""
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    out = re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")
    return (out[:maxlen].rstrip("-")) or "concept"


def unique_slug(db: OrmSession, base: str, taken: set[str]) -> str:
    """A slug nothing else holds -- in this run OR already in the database.

    Checking only the in-memory set would collide with a previous run, and the
    column is unique, so the collision arrives as an IntegrityError halfway
    through a 240-call pass. Cheap to check, expensive to hit.
    """
    slug = base
    n = 2
    while slug in taken or db.scalar(select(Concept.id).where(Concept.slug == slug)):
        suffix = f"-{n}"
        slug = base[: 80 - len(suffix)].rstrip("-") + suffix
        n += 1
    taken.add(slug)
    return slug


# ---------------------------------------------------------------------------
# similarity
# ---------------------------------------------------------------------------

def cosine(a: list[float], b: list[float]) -> float:
    """Both vectors come from fastembed unit-normalised, so this is a dot
    product. Written out anyway -- a future model that does not normalise would
    otherwise silently return numbers above 1 and match everything."""
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def duplicate_of(
    name: str,
    summary: str | None,
    candidates: list[tuple[Concept, float]],
) -> Concept | None:
    """Which existing concept, if any, this one is a restatement of.

    Only ever called on names the cheap gate already flagged, so this is a
    handful of calls per chapter rather than one per pair. A failure here
    returns None -- keeping a near-duplicate is a mistake a human can see in
    the concept list, whereas a wrong merge deletes a syllabus line silently.
    """
    if not candidates:
        return None
    by_slug = {c.slug: c for c, _ in candidates}
    lines = []
    for concept, score in candidates:
        block = [f"- slug: {concept.slug}", f"  name: {concept.name}"]
        if concept.summary:
            block.append(f"  summary: {concept.summary}")
        block.append(f"  name similarity: {score:.3f}")
        lines.extend(block)
    listing = "\n".join(lines)

    candidate_text = f"name: {name}"
    if summary:
        candidate_text += f"\nsummary: {summary}"

    try:
        result = complete(
            prompts.render(
                "concepts_same", candidate=candidate_text, existing=listing
            ),
            json_schema=SAME_SCHEMA,
            max_tokens=120,
        )
        slug = json.loads(result.text).get("duplicate_of")
    except (AllProvidersFailed, json.JSONDecodeError, TypeError, KeyError):
        return None
    return by_slug.get(slug) if isinstance(slug, str) else None


# ---------------------------------------------------------------------------
# the pass
# ---------------------------------------------------------------------------

def windows(chunks: list[Chunk], size: int):
    """Consecutive chunks, grouped by chapter, in page order.

    A window never straddles a chapter boundary. One that did would ask the
    model to name the concepts of two unrelated sections at once, and would
    produce a page range spanning the join.
    """
    by_chapter: list[tuple[str, list[Chunk]]] = []
    for c in chunks:
        label = c.chapter or "(front matter)"
        if by_chapter and by_chapter[-1][0] == label:
            by_chapter[-1][1].append(c)
        else:
            by_chapter.append((label, [c]))

    for chapter, rows in by_chapter:
        if SKIP_CHAPTERS.match(chapter):
            continue
        for i in range(0, len(rows), size):
            group = rows[i : i + size]
            if group:
                yield chapter, group


def derive(
    db: OrmSession,
    course: Course,
    material: Material,
    *,
    window_size: int,
    max_windows: int | None,
    dry_run: bool,
) -> int:
    chunks = db.scalars(
        select(Chunk)
        .where(Chunk.material_id == material.id)
        .order_by(Chunk.page_no, Chunk.id)
    ).all()
    if not chunks:
        log(f"  material {material.id} has no chunks -- ingest it first")
        return 1

    prereq = course.prerequisites[0] if course.prerequisites else None
    usable = sum(len(g) for _, g in windows(list(chunks), window_size))
    log(f"  {len(chunks)} chunks, {usable} after skipping front matter, "
        f"window {window_size}")
    log(f"  prerequisite course: {prereq.code if prereq else '(none -- nothing '
        f'will be marked as a prerequisite)'}")
    log()

    # Everything already derived for this course, so a re-run adds rather than
    # duplicates. Seeded concepts are in here too: the derivation must not
    # produce a second "Class inheritance in Python" next to the hand-written
    # one that the whole golden path depends on.
    existing = db.scalars(
        select(Concept)
        .join(Topic, Topic.id == Concept.topic_id)
        .where(Topic.course_id == course.id)
    ).all()
    accepted: list[tuple[Concept, list[float]]] = []
    if existing:
        vectors = embed.embed_documents([c.name for c in existing])
        accepted = list(zip(existing, vectors))
        log(f"  {len(existing)} concepts already on this course "
            f"({sum(1 for c in existing if c.source == 'seed')} seeded) -- "
            f"they are deduplication targets, not rewrite targets")
    taken_slugs = {c.slug for c in existing}

    topics: dict[str, Topic] = {}
    added = merged = empty = failed = gated = 0
    seen_windows = 0

    current_chapter: str | None = None
    for chapter, group in windows(list(chunks), window_size):
        if max_windows is not None and seen_windows >= max_windows:
            break
        seen_windows += 1

        # Commit at each chapter boundary. A full pass over the Django book is
        # ~240 model calls and twenty-odd minutes; holding one transaction open
        # across all of it against a shared remote database means a crash at
        # window 230 throws away 229 windows of work, and means every other
        # session waits behind it. A chapter is the natural unit -- it is also
        # the topic, so a commit never lands a concept whose topic is missing.
        if chapter != current_chapter:
            if current_chapter is not None and not dry_run:
                db.commit()
            current_chapter = chapter
            log(f"  -- {chapter}")

        pages = f"{group[0].page_no}-{group[-1].page_no}"
        context = "\n\n".join(c.text for c in group)
        try:
            result = complete(
                prompts.render(
                    "concepts_derive",
                    chapter=chapter,
                    pages=pages,
                    context=context,
                    # The prerequisite question is only answerable against a
                    # named prior course and a named subject. Asking "is this a
                    # prerequisite?" in the abstract got `false` for Python
                    # class inheritance -- which is one of the hand-written
                    # prerequisites this very course tests.
                    prerequisite_course=(
                        prereq.title if prereq else "an earlier programming course"
                    ),
                    subject=course.title,
                ),
                json_schema=DERIVE_SCHEMA,
                max_tokens=900,
            )
            parsed = json.loads(result.text).get("concepts") or []
        except (AllProvidersFailed, json.JSONDecodeError, TypeError, KeyError) as exc:
            # One bad window must not cost the other 241. The corpus is not
            # going anywhere; re-run and the cache replays every good call.
            failed += 1
            log(f"    ! {chapter[:36]:<38} p{pages:<10} {type(exc).__name__}")
            continue

        if not isinstance(parsed, list) or not parsed:
            empty += 1
            continue

        for item in parsed:
            name = str(item.get("name", "")).strip()
            if not name or len(name) > 200:
                continue
            summary = str(item.get("summary", "")).strip() or None
            is_prereq = bool(item.get("prerequisite")) and prereq is not None

            vector = embed.embed_document(name)
            near = sorted(
                ((c, cosine(vector, other)) for c, other in accepted),
                key=lambda pair: pair[1],
                reverse=True,
            )
            candidates = [(c, sc) for c, sc in near if sc >= MERGE_CANDIDATE][
                :MAX_CANDIDATES
            ]
            gated += len(candidates) > 0
            best = duplicate_of(name, summary, candidates)

            if best is not None:
                merged += 1
                log(f"    = {name[:44]:<46} -> {best.name[:40]} "
                    f"({'seeded' if best.source == 'seed' else 'derived'})")
                # The duplicate is evidence the concept spans more of the book
                # than the first window showed. Widen, never overwrite -- and
                # never touch a seeded row, which a human wrote on purpose.
                if best.source == "derived" and not dry_run:
                    if best.page_start is None or group[0].page_no < best.page_start:
                        best.page_start = group[0].page_no
                    if best.page_end is None or group[-1].page_no > best.page_end:
                        best.page_end = group[-1].page_no
                continue

            if chapter not in topics:
                slug = slugify(chapter, maxlen=80)
                row = db.scalar(
                    select(Topic).where(Topic.course_id == course.id, Topic.slug == slug)
                )
                if row is None:
                    row = Topic(course_id=course.id, slug=slug, name=chapter,
                                source="derived")
                    if not dry_run:
                        db.add(row)
                        db.flush()
                topics[chapter] = row

            concept = Concept(
                topic_id=topics[chapter].id,
                slug=unique_slug(db, slugify(name), taken_slugs),
                name=name,
                summary=summary,
                source="derived",
                material_id=material.id,
                page_start=group[0].page_no,
                page_end=group[-1].page_no,
                prerequisite_course_id=prereq.id if is_prereq else None,
            )
            if not dry_run:
                db.add(concept)
                db.flush()
            accepted.append((concept, vector))
            added += 1
            flag = " [prerequisite]" if is_prereq else ""
            log(f"    + {name[:56]:<58} p{pages:<10}{flag}")

    if not dry_run:
        db.commit()

    log()
    log(f"  windows processed  {seen_windows}")
    log(f"  concepts added     {added}")
    log(f"  merged as dupes    {merged}")
    log(f"  decider calls      {gated}   (names the 0.75 gate flagged)")
    log(f"  windows with none  {empty}")
    log(f"  windows failed     {failed}")
    if dry_run:
        log("\n  --dry-run: nothing was written.")
    return 0


def make_diagnostic_items(db: OrmSession, course: Course, budget: int) -> int:
    """Give derived prerequisite concepts a question, so gaps can be found.

    **This does not change the golden path, and the reason is ordering, not
    restraint.** `GET /student/diagnostic` serves items whose concept is
    `source == "seed"` first, so however many of these exist, page one is still
    the eight hand-written questions the demo answers. These are page two.

    Only PREREQUISITE concepts get one. A question about material this course
    is about to teach is not a diagnostic -- finding it absent is expected, and
    reporting it as a gap would bury the real gaps in noise.

    A concept whose pages cannot support a fair question is SKIPPED, on the
    model's own say-so. A weak prerequisite question is worse than none: it
    manufactures a gap the student does not have and sends them a remedial
    lesson for something they already understand.
    """
    concepts = db.scalars(
        select(Concept)
        .join(Topic, Topic.id == Concept.topic_id)
        .where(Topic.course_id == course.id,
               Concept.source == "derived",
               Concept.prerequisite_course_id.is_not(None),
               Concept.id.not_in(
                   select(DiagnosticItem.concept_id).where(
                       DiagnosticItem.course_id == course.id
                   )
               ))
        .order_by(Concept.id)
        .limit(budget)
    ).all()

    if not concepts:
        log("  every derived prerequisite already has an item -- nothing to do")
        return 0

    log(f"  {len(concepts)} derived prerequisite concepts without an item")
    written = skipped = failed = 0
    for concept in concepts:
        chunks = db.scalars(
            select(Chunk)
            .where(Chunk.material_id == concept.material_id,
                   Chunk.page_no >= (concept.page_start or 0),
                   Chunk.page_no <= (concept.page_end or 10**9))
            .order_by(Chunk.page_no, Chunk.id)
            .limit(10)
        ).all()
        if not chunks:
            skipped += 1
            continue

        try:
            result = complete(
                prompts.render(
                    "diagnostic_item",
                    concept=concept.name,
                    summary=concept.summary or "",
                    pages=f"{concept.page_start}-{concept.page_end}",
                    context="\n\n".join(c.text for c in chunks),
                ),
                json_schema=ITEM_SCHEMA,
                max_tokens=700,
            )
            data = json.loads(result.text)
        except (AllProvidersFailed, json.JSONDecodeError, TypeError) as exc:
            failed += 1
            log(f"    ! {concept.name[:52]:<54} {type(exc).__name__}")
            continue

        options = data.get("options") or []
        answer = str(data.get("correct_answer", "")).strip()
        if (data.get("skip") or len(options) != 4 or not answer
                or answer not in options):
            # Every one of those is a malformed question, and a malformed
            # prerequisite question is a gap invented out of nothing.
            skipped += 1
            log(f"    - {concept.name[:52]:<54} skipped")
            continue

        db.add(DiagnosticItem(
            course_id=course.id,
            concept_id=concept.id,
            prompt=str(data.get("prompt", "")).strip()[:2000],
            kind="mcq",
            options={"choices": [str(o) for o in options]},
            correct_answer=answer[:300],
        ))
        written += 1
        log(f"    + {concept.name[:52]:<54} item written")

    db.commit()
    log()
    log(f"  items written      {written}")
    log(f"  concepts skipped   {skipped}   (the material could not carry a fair question)")
    log(f"  failed             {failed}")
    return 0


def reset_derived(db: OrmSession, course: Course) -> int:
    """Delete this course's derived concepts and topics, so a pass can re-run
    from scratch after the prompt changes.

    **Nothing with dependents is ever deleted.** Exactly the rule
    `prune_removed()` follows in seed.py, for the same reason: a concept
    carrying a student's gap, a mastery row, a practice item or a diagnostic
    item has real history behind it, and a re-derivation is not the authority
    to throw that away. Those are reported and kept.

    Seeded content is untouched -- this only ever sees `source == "derived"`.
    """
    from app.models import DiagnosticItem, Gap, Mastery, PracticeItem

    concepts = db.scalars(
        select(Concept)
        .join(Topic, Topic.id == Concept.topic_id)
        .where(Topic.course_id == course.id, Concept.source == "derived")
    ).all()

    kept, gone = [], 0
    for c in concepts:
        deps = {
            "gaps": db.scalar(select(func.count()).select_from(Gap)
                              .where(Gap.concept_id == c.id)),
            "mastery": db.scalar(select(func.count()).select_from(Mastery)
                                 .where(Mastery.concept_id == c.id)),
            "practice": db.scalar(select(func.count()).select_from(PracticeItem)
                                  .where(PracticeItem.concept_id == c.id)),
            "diagnostic": db.scalar(select(func.count()).select_from(DiagnosticItem)
                                    .where(DiagnosticItem.concept_id == c.id)),
        }
        if any(deps.values()):
            kept.append((c, {k: v for k, v in deps.items() if v}))
            continue
        db.delete(c)
        gone += 1

    db.flush()
    topics_gone = 0
    for t in db.scalars(
        select(Topic).where(Topic.course_id == course.id, Topic.source == "derived")
    ).all():
        if not db.scalar(select(func.count()).select_from(Concept)
                         .where(Concept.topic_id == t.id)):
            db.delete(t)
            topics_gone += 1

    db.commit()
    log(f"  deleted {gone} derived concepts and {topics_gone} now-empty derived topics")
    for c, deps in kept:
        log(f"  KEPT {c.name[:50]:<52} {deps}")
    if kept:
        log(f"  {len(kept)} kept because something depends on them -- "
            f"a re-derivation is not the authority to delete a student's history")
    return 0


def report(db: OrmSession) -> int:
    rows = db.execute(
        select(Course.code, Concept.source, func.count(Concept.id))
        .join(Topic, Topic.course_id == Course.id)
        .join(Concept, Concept.topic_id == Topic.id)
        .group_by(Course.code, Concept.source)
        .order_by(Course.code, Concept.source)
    ).all()
    log("concepts by course and source:")
    for code, source, n in rows:
        log(f"  {code:<10} {source:<10} {n:>5}")

    prereq = db.scalar(
        select(func.count()).select_from(Concept)
        .where(Concept.source == "derived", Concept.prerequisite_course_id.is_not(None))
    )
    log(f"\nderived concepts marked as prerequisites: {prereq}")
    log("(only these are diagnostic-testable -- see student.get_diagnostic)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--course", help="course code, e.g. CSW2")
    ap.add_argument("--material", type=int, help="material id to read")
    ap.add_argument("--window-size", type=int, default=DEFAULT_WINDOW)
    ap.add_argument("--windows", type=int, default=None,
                    help="stop after N windows -- a bounded first pass")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--reset-derived", action="store_true",
                    help="delete this course's derived concepts (never any with "
                         "dependents, never seeded ones) so a pass can re-run")
    ap.add_argument("--diagnostic", type=int, metavar="N", default=None,
                    help="after deriving, write diagnostic items for up to N "
                         "derived PREREQUISITE concepts that do not have one")
    args = ap.parse_args()

    db = get_sessionmaker()()
    try:
        if args.report:
            return report(db)
        if not args.course:
            ap.error("--course is required (or use --report)")
        if not args.material and not args.reset_derived:
            ap.error("--material is required unless --reset-derived")

        course = db.scalar(select(Course).where(Course.code == args.course))
        if course is None:
            log(f"no course with code {args.course}")
            return 1
        # Before the material check: a reset is about the course's derived
        # rows, and does not care which book they came out of.
        if args.reset_derived:
            log(f"resetting derived concepts for {course.code}")
            return reset_derived(db, course)

        material = db.get(Material, args.material)
        if material is None or material.course_id != course.id:
            log(f"material {args.material} is not a material of {args.course}")
            return 1

        log(f"deriving concepts for {course.code} from "
            f"material {material.id} ({material.title})")
        code = derive(
            db, course, material,
            window_size=args.window_size,
            max_windows=args.windows,
            dry_run=args.dry_run,
        )
        if code == 0 and args.diagnostic and not args.dry_run:
            log()
            log(f"writing diagnostic items (budget {args.diagnostic})")
            code = make_diagnostic_items(db, course, args.diagnostic)
        return code
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
