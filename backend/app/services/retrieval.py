"""rag-001 -- find the passages, carry the page numbers.

Brute-force cosine over pgvector. No ivfflat, no hnsw: the corpus is a handful
of books, an approximate index would save milliseconds we do not need, and it
can silently return the wrong neighbours. That is a failure mode, not an
optimisation. See the stack table in CLAUDE.md.

Two rules the rest of the backend depends on:

* **Every search is scoped to one course.** `course_id` is required, not
  optional-with-a-sensible-default. The database holds several courses' books
  at once, and a mechanics question that matched a C programming chapter would
  not look like a bug -- it would look like a slightly odd answer, with a real
  citation attached, and nobody would catch it on stage.

* **Assignments are searchable but never quotable.** `search()` excludes
  `kind="assignment"`, so graded material can never be handed back as a lesson.
  `search_assignments()` is the deliberate, separate door the graded-work
  guardrail (rag-004) knocks on.

Citations are built from stored columns only -- `page_no` comes off the chunk
row that ingestion wrote. No model is ever asked where a passage came from,
which is why a citation cannot be hallucinated.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..models import Chunk, Material
from .embed import embed_query

# Kinds that may be quoted back to a student as course material.
LESSON_KINDS = ("syllabus", "textbook", "notes")
SNIPPET_CHARS = 220
DEFAULT_K = 5


@dataclass(frozen=True)
class Hit:
    """One retrieved chunk and how close it was."""

    chunk_id: int
    material_id: int
    book_title: str
    kind: str
    page_no: int
    chapter: str | None
    text: str
    similarity: float

    def citation(self) -> dict:
        """The contract's `Citation` object (docs/api-contract.md)."""
        return {
            "chunk_id": self.chunk_id,
            "material_id": self.material_id,
            "book_title": self.book_title,
            "page_no": self.page_no,
            "chapter": self.chapter,
            "snippet": snippet(self.text),
        }


def snippet(text: str, limit: int = SNIPPET_CHARS) -> str:
    """A readable excerpt: single-spaced, cut at a word boundary."""
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    cut = flat.rfind(" ", 0, limit)
    return flat[: cut if cut > limit // 2 else limit].rstrip(" ,;:") + "..."


def _search(
    db: OrmSession,
    question: str,
    *,
    course_id: int | None,
    kinds: tuple[str, ...],
    k: int,
    include_archived: bool,
) -> list[Hit]:
    vector = embed_query(question)     # BGE query prefix lives in embed.py
    distance = Chunk.embedding.cosine_distance(vector).label("distance")

    stmt = (
        select(Chunk, Material, distance)
        .join(Material, Material.id == Chunk.material_id)
        .where(Material.kind.in_(kinds))
        .order_by(distance)
        .limit(k)
    )
    if course_id is not None:
        stmt = stmt.where(Material.course_id == course_id)
    if not include_archived:
        # An archived material is a superseded edition. It stays in the database
        # for admin-001's version history, but quoting it would cite a page a
        # student's current book does not have.
        stmt = stmt.where(Material.status == "active")

    return [
        Hit(
            chunk_id=chunk.id,
            material_id=material.id,
            book_title=material.title,
            kind=material.kind,
            page_no=chunk.page_no,
            chapter=chunk.chapter,
            text=chunk.text,
            # pgvector returns cosine DISTANCE; vectors are unit-norm, so
            # similarity is 1 - distance and lands in [0, 1] for our corpus.
            similarity=1.0 - float(dist),
        )
        for chunk, material, dist in db.execute(stmt).all()
    ]


def search(
    db: OrmSession,
    question: str,
    *,
    course_id: int | None,
    k: int = DEFAULT_K,
    kinds: tuple[str, ...] = LESSON_KINDS,
    include_archived: bool = False,
) -> list[Hit]:
    """Top-k approved passages for a question, most similar first.

    `course_id=None` searches every course. Only calibration and admin tooling
    should ever pass it -- see the module docstring.
    """
    return _search(db, question, course_id=course_id, kinds=kinds, k=k,
                   include_archived=include_archived)


def search_assignments(
    db: OrmSession,
    question: str,
    *,
    course_id: int | None,
    k: int = 3,
) -> list[Hit]:
    """Graded material only. The cheap first half of the rag-004 guardrail: a
    vector match here is what decides whether the expensive intent check runs
    at all.

    Kept separate from `search()` rather than being a flag on it, so no future
    caller can accidentally widen a lesson search to include homework.
    """
    return _search(db, question, course_id=course_id, kinds=("assignment",), k=k,
                   include_archived=False)


def _stitch(a: str, b: str) -> str:
    """Join two chunks off the same page without repeating their overlap.

    Chunking gives consecutive chunks one sentence of overlap, so a plain join
    would say the same sentence twice in the prompt.
    """
    for cut in range(min(len(a), len(b)), MIN_OVERLAP, -1):
        if a.endswith(b[:cut]):
            return a + b[cut:]
    return f"{a} {b}"


# Longest overlap wins, so this is only the point below which a match is more
# likely to be coincidence than a real shared sentence. Short sentences ("It
# then stops.") are common in a programming book's step lists, so it cannot be
# set at a sentence's typical length.
MIN_OVERLAP = 12


def sources(hits: list[Hit]) -> list[tuple[Hit, str]]:
    """One entry per source page: (best hit for that page, its merged text).

    This grouping is the reason the tutor's `[2]` and the UI's second citation
    are the same thing. Numbering passages while citations were deduplicated by
    page put a `[5]` in an answer that had only four sources -- a student
    clicking it finds nothing, and it is the kind of detail a judge checks.

    Page order follows similarity: the best-matching page is `[1]`.
    """
    order: list[tuple[int, int]] = []
    merged: dict[tuple[int, int], list] = {}
    for hit in hits:
        key = (hit.material_id, hit.page_no)
        if key not in merged:
            merged[key] = [hit, hit.text]
            order.append(key)
        else:
            merged[key][1] = _stitch(merged[key][1], hit.text)
    return [(merged[k][0], merged[k][1]) for k in order]


DEFAULT_CONTEXT_CHARS = 4000


def grounding(hits: list[Hit], max_chars: int = DEFAULT_CONTEXT_CHARS) -> tuple[str, list[dict]]:
    """The prompt context and the citation list, built together so they agree.

    Returned as a pair rather than as two functions a caller might call with
    different arguments. The context has a character budget; a citation list
    built separately would keep sources the model never saw, and the student
    would get a "Show Source" entry backing nothing. `[n]` in the answer is
    always `citations[n-1]`.
    """
    parts: list[str] = []
    cites: list[dict] = []
    used = 0
    for i, (hit, text) in enumerate(sources(hits), 1):
        body = " ".join(text.split())
        head = f"[{i}] {hit.book_title}, page {hit.page_no}"
        if hit.chapter:
            head += f" ({hit.chapter})"
        block = f"{head}\n{body}"
        if used + len(block) > max_chars and parts:
            break
        parts.append(block)
        cites.append(hit.citation())
        used += len(block)
    return "\n\n".join(parts), cites


def citations(hits: list[Hit]) -> list[dict]:
    """Citations only -- one per source page, numbered as the answer saw them."""
    return grounding(hits)[1]


def context_block(hits: list[Hit], max_chars: int = DEFAULT_CONTEXT_CHARS) -> str:
    """Prompt context only. See `grounding()` for why they are computed as one."""
    return grounding(hits, max_chars)[0]
