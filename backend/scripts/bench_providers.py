"""Check every provider works, and how fast, then print a recommended order.

    .venv/Scripts/python.exe backend/scripts/bench_providers.py

Run this whenever a key or model id changes, and once before demo day. The
chain in app/providers/__init__.py is ordered by MEASURED latency, not by
preference, because a judge asking a novel question waits for the first
uncached call.

Two failure modes this catches that nothing else does:

  * A model id that is a display name rather than an API id. "Gemini 3.6 Flash"
    fails with HTTP 400 and "Llama 3.3 70B" with 404 - both of which look like
    a bad key until you read the response body.
  * A reasoning model whose thinking consumes the entire token budget, leaving
    empty content and finishReason=MAX_TOKENS with no error at all.
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config
from app.providers.base import ProviderError
from app.providers.http_providers import gemini, glm, groq

PROMPT = "In one sentence, why does a block at constant velocity have zero net force?"
RUNS = 3


def main() -> None:
    candidates = [
        ("groq", groq(config.FALLBACK_MODEL_GROQ)),
        ("groq-alt", groq(config.FALLBACK_MODEL_GROQ_ALTERNATIVE)),
        ("gemini", gemini()),
        ("glm", glm()),
    ]

    print(f"{'provider':10} {'model':26} {'ok':>3} {'median ms':>10}  note")
    print("-" * 82)

    results = []
    for label, p in candidates:
        if not getattr(p, "configured", True):
            print(f"{label:10} {str(p.model)[:26]:26} {'-':>3} {'-':>10}  not configured")
            continue

        times, note = [], ""
        for _ in range(RUNS):
            try:
                t = time.time()
                out = p.complete(PROMPT)
                times.append((time.time() - t) * 1000)
                if not note:
                    note = out.strip().replace("\n", " ")[:34]
            except ProviderError as exc:
                note = "FAIL " + str(exc).encode("ascii", "replace").decode()[:44]
                break

        median = statistics.median(times) if times else None
        shown = f"{median:.0f}" if median else "-"
        print(f"{label:10} {str(p.model)[:26]:26} {len(times):>3} {shown:>10}  {note}")
        if median:
            results.append((median, label, p.name))

    if not results:
        sys.exit("\nNo provider works. Check keys and model ids before doing anything else.")

    results.sort()
    print()
    print("Recommended order (fastest working first):")
    for i, (ms, label, name) in enumerate(results, 1):
        print(f"  {i}. {label:10} {ms:7.0f} ms")

    fastest = results[0]
    print()
    print(f"Suggested PROVIDER={fastest[2]}")
    print("If this differs from BY_SPEED in app/providers/__init__.py, update it there.")

    slow = [r for r in results if r[0] > 10_000]
    if slow:
        print()
        print("WARNING - these take over 10s and should never lead the chain:")
        for ms, label, _ in slow:
            print(f"  {label} at {ms:.0f} ms")


if __name__ == "__main__":
    main()
