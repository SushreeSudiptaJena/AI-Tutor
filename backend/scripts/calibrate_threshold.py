"""Find the right ALIGNMENT_REFUSAL_THRESHOLD for the corpus you actually have.

    .venv/Scripts/python.exe backend/scripts/calibrate_threshold.py --course CS-C

Why this exists
---------------
Embedding similarity has a high floor. With bge-small-en-v1.5, two texts about
completely different subjects still score around 0.4-0.5, and an off-topic
question from a NEARBY field can score as high as a covered one. So a threshold
guessed out of thin air either never refuses (too low) or refuses everything
(too high). Both failures are silent, and the low one is worse: "it answered"
looks exactly like success.

The threshold is a property of the ingested books, not a constant. Re-run this
after every ingest -- a new corpus moves it.

    --course CODE      which course's material to measure (default: the primary)
    --questions FILE   JSON: {"covered": [...], "off_topic": [...]}

Without --questions it uses the built-in physics set, which only makes sense
against the stand-in corpus. For any real subject, write the file: eight
questions you know the book covers and eight it does not, at least one of them
from a NEIGHBOURING topic. Those are the hard ones, and the ones a judge tries.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models import Chunk, Course, Material
from app.services import retrieval

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"

DEFAULT_COVERED = [
    "Why does a block moving at constant speed need no net force?",
    "How do I split a vector into components?",
    "What is Newton's second law?",
]
DEFAULT_OFF_TOPIC = [
    "Explain Lagrangian mechanics and the principle of least action",
    "What is photosynthesis in plant cells?",
    "Who won the football world cup in 2018?",
]


def load_questions(path: Path | None) -> tuple[list[str], list[str]]:
    if path is None:
        return DEFAULT_COVERED, DEFAULT_OFF_TOPIC
    data = json.loads(path.read_text(encoding="utf-8"))
    covered, off = data.get("covered", []), data.get("off_topic", [])
    if not covered or not off:
        sys.exit(f"{path} needs a non-empty 'covered' and 'off_topic' list.")
    return covered, off


def resolve_course(db, code: str | None) -> Course:
    if not code:
        code = json.loads((SEED_DIR / "course.json").read_text(encoding="utf-8"))["primary_course"]
    course = db.scalar(select(Course).where(Course.code == code))
    if course is None:
        sys.exit(f"No course with code {code!r}.")
    return course


def top_similarity(db, question: str, course_id: int) -> tuple[float, str]:
    """Uses the real retrieval path, so this measures what the tutor will see --
    including the exclusion of assignment material and archived editions."""
    hits = retrieval.search(db, question, course_id=course_id, k=1)
    if not hits:
        return 0.0, "(nothing retrieved)"
    top = hits[0]
    return top.similarity, f"{top.book_title}, p.{top.page_no}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--course")
    ap.add_argument("--questions", type=Path)
    args = ap.parse_args()

    covered_qs, off_qs = load_questions(args.questions)

    db = get_sessionmaker()()
    try:
        course = resolve_course(db, args.course)
        n = db.scalar(
            select(Chunk.id).join(Material)
            .where(Material.course_id == course.id).limit(1)
        )
        if n is None:
            sys.exit(f"No chunks for {course.code}. Run ingestion first (ingest-001).")

        print(f"corpus: {course.code} - {course.title}\n")
        print(f"{'kind':10} {'top-sim':>8}  {'source':38} question")
        print("-" * 100)

        cov, off = [], []
        for label, questions, bucket in (("COVERED", covered_qs, cov),
                                         ("OFF-TOPIC", off_qs, off)):
            for q in questions:
                sim, source = top_similarity(db, q, course.id)
                bucket.append(sim)
                print(f"{label:10} {sim:8.4f}  {source[:38]:38} {q[:44]}")

        lo, hi = min(cov), max(off)
        print()
        print(f"lowest covered      : {lo:.4f}")
        print(f"highest off-topic   : {hi:.4f}")
        print(f"margin              : {lo - hi:+.4f}")
        print()

        if lo <= hi:
            print("NO CLEAN SEPARATION.")
            print("Retrieval similarity alone cannot tell these apart, so the")
            print("entailment half of the evidence check is doing the real work.")
            print("Do not simplify evidence.py down to top-similarity.")
            print()

        # Sit just under the weakest covered question rather than midway: a
        # false refusal on material we DO have is the more visible failure, and
        # the entailment check still catches the near-domain cases this lets in.
        suggested = max(0.0, min((lo + hi) / 2, lo - 0.01))
        print(f"SUGGESTED ALIGNMENT_REFUSAL_THRESHOLD = {suggested:.2f}")
        print()
        print("Put that in .env. Then verify by hand through the real endpoint:")
        print("one covered question must answer, one off-topic must refuse.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
