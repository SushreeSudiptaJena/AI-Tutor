"""Canned responses. No network, no keys, fully deterministic.

Set PROVIDER=mock to run the entire golden path with the wifi off. This is not
a toy: it is the last link in the fallback chain, so the demo degrades to
"answers are generic" rather than "the app is broken".

It also lets the test suite exercise every service that calls a model without a
network, keeping the no-DB/no-network rule for pytest.
"""

from __future__ import annotations

import json
import re

from .base import ProviderError  # noqa: F401  (kept for interface symmetry)

_EXPLANATION = (
    "Motion does not require a force; only a change in motion does. When a block "
    "slides at constant velocity, the applied push and the friction force are equal "
    "in magnitude and opposite in direction, so they cancel. The net force is "
    "therefore zero even though the block is moving."
)

_HINTS = [
    "Start by drawing a free-body diagram and labelling every force.",
    "Resolve each force into components along and perpendicular to the motion.",
    "Ask what the acceleration must be, then apply F_net = m a.",
]


def _looks_like(prompt: str, system: str, *words: str) -> bool:
    blob = f"{system}\n{prompt}".lower()
    return any(w in blob for w in words)


class MockProvider:
    """Shapes its answer to what was asked, so callers get something usable."""

    name = "mock"
    model = "mock-1"

    def complete(
        self,
        prompt: str,
        *,
        system: str = "",
        json_schema: dict | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> str:
        if json_schema is not None:
            return json.dumps(self._for_schema(prompt, system, json_schema))
        if _looks_like(prompt, system, "hint", "scaffold", "approach"):
            return "\n".join(f"- {h}" for h in _HINTS)
        return _EXPLANATION

    # -- structured output ---------------------------------------------------

    def _for_schema(self, prompt: str, system: str, schema: dict) -> dict:
        props = (schema.get("properties") or {}) if isinstance(schema, dict) else {}

        # Entailment check: "how well do these sources support this answer?"
        if "entailment" in props or _looks_like(prompt, system, "entail", "supported by"):
            return {"entailment": 0.86, "reason": "mock: sources support the answer"}

        # Intent classification for the graded-work guardrail.
        if "intent" in props or _looks_like(prompt, system, "intent", "solve or understand"):
            solve = _looks_like(prompt, "", "solve", "calculate", "find the", "compute", "answer to q")
            return {"intent": "solve" if solve else "understand", "confidence": 0.9}

        # Misconception pick from a supplied candidate list.
        if "misconception_slug" in props:
            return {"misconception_slug": None, "confidence": 0.0,
                    "reason": "mock: no confident match"}

        # Practice generation. `distractors` is not optional decoration: a
        # generated item whose wrong answers map to no misconception produces
        # the demo's weakest moment -- a wrong answer, and silence. With the
        # wifi off, the mock still has to hand back something diagnosable.
        if "items" in props:
            return {"items": [{
                "prompt": "A 2 kg block slides at constant velocity across a rough floor. "
                          "What is the net force on it?",
                "kind": "mcq",
                "options": ["0 N", "6 N", "20 N", "24 N"],
                "correct_answer": "0 N",
                "problem_type": "net-force-constant-velocity",
                "distractors": {"6 N": "velocity-implies-force"},
            }]}

        # Scaffolded hints for the graded-work guardrail (rag-004).
        if "hints" in props:
            return {"hints": _HINTS}

        # Syllabus coverage (student-008). The generic array fallback below
        # would return [], which the service reads as "no verdict for any
        # concept" and therefore "every prerequisite is a gap" -- a maximal gap
        # list with the wifi off, which looks like a real result and is not one.
        # So the mock answers the shape properly: it marks a prerequisite
        # covered when its slug or name actually appears in the uploaded text,
        # which makes the offline path exercise both branches.
        if "concepts" in props:
            # Only the uploaded syllabus counts. Searching the whole prompt
            # matched every concept against its own name in the listing above,
            # so everything came back covered and no gap was ever produced.
            marker = "syllabus the student uploaded"
            lowered = prompt.lower()
            seen = lowered[lowered.rindex(marker):] if marker in lowered else lowered
            covered = []
            for slug in re.findall(r"^- `([a-z0-9-]+)`", prompt, re.MULTILINE):
                words = [w for w in slug.split("-") if len(w) > 3]
                hit = bool(words) and all(w in seen for w in words)
                covered.append({
                    "slug": slug,
                    "covered": hit,
                    "evidence": f"mock: matched {slug!r} in the upload" if hit else "",
                })
            return {"concepts": covered}

        # Generic explanation object.
        out: dict = {}
        for key, spec in props.items():
            t = spec.get("type") if isinstance(spec, dict) else None
            if key in ("body", "text", "answer", "explanation", "title"):
                out[key] = _EXPLANATION
            elif key == "hints":
                out[key] = _HINTS
            elif t == "array":
                out[key] = []
            elif t == "number":
                out[key] = 0.0
            elif t == "integer":
                out[key] = 0
            elif t == "boolean":
                out[key] = True
            else:
                out[key] = "mock"
        return out or {"text": _EXPLANATION}
