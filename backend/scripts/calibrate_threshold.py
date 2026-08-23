"""Find the right ALIGNMENT_REFUSAL_THRESHOLD for the real corpus.

    .venv/Scripts/python.exe backend/scripts/calibrate_threshold.py

Why this exists
---------------
Embedding similarity has a high floor. With bge-small-en-v1.5, two texts about
completely different subjects still score around 0.4-0.5, and an off-topic
question from a NEARBY field can score as high as a covered one. So a threshold
guessed out of thin air either never refuses (too low) or refuses everything
(too high). Both failures are silent.

Run this after ingesting the demo corpus. Edit COVERED and OFF_TOPIC below to
match the subject, then use the threshold it recommends.

Needs the corpus already ingested (ingest-001) and a reachable database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models import Chunk, Material
from app.services.embed import embed_query  # must apply the BGE query prefix

# ---------------------------------------------------------------------------
# Edit these for your subject. 5-8 of each is plenty.
# ---------------------------------------------------------------------------
COVERED = [
    "Why does a block moving at constant speed need no net force?",
    "How do I split a vector into components?",
    "What is Newton's second law?",
]

# Include at least one question from a NEARBY field. Those are the hard ones,
# and the ones a judge is most likely to try.
OFF_TOPIC = [
    "Explain Lagrangian mechanics and the principle of least action",
    "What is photosynthesis in plant cells?",
    "Who won the football world cup in 2018?",
]
# ---------------------------------------------------------------------------


def top_similarity(db, question: str) -> float:
    vec = embed_query(question)
    row = db.execute(
        select(Chunk.embedding.cosine_distance(vec).label("dist"))
        .join(Material)
        .where(Material.kind != "assignment")
        .order_by("dist")
        .limit(1)
    ).first()
    return 0.0 if row is None else 1.0 - float(row[0])


def main() -> None:
    db = get_sessionmaker()()
    try:
        n = db.execute(select(Chunk.id).limit(1)).first()
        if n is None:
            sys.exit("No chunks in the database. Run ingestion first (ingest-001).")

        print(f"{'kind':10} {'top-sim':>8}  question")
        print("-" * 72)
        cov, off = [], []
        for q in COVERED:
            s = top_similarity(db, q)
            cov.append(s)
            print(f"{'COVERED':10} {s:8.4f}  {q[:48]}")
        for q in OFF_TOPIC:
            s = top_similarity(db, q)
            off.append(s)
            print(f"{'OFF-TOPIC':10} {s:8.4f}  {q[:48]}")

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
            print("Weight it higher, and do not rely on top-similarity alone.")
            suggested = (lo + hi) / 2
        else:
            suggested = (lo + hi) / 2

        print(f"SUGGESTED ALIGNMENT_REFUSAL_THRESHOLD = {suggested:.2f}")
        print()
        print("Put that in .env. Then verify by hand: ask one covered question")
        print("and one off-topic question through the real endpoint and confirm")
        print("the first answers and the second refuses.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
