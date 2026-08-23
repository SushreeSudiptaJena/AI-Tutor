"""Canned responses. No network, no keys, fully deterministic.

Set PROVIDER=mock to run the entire golden path with the wifi off. This is not
a toy: it is the last link in the fallback chain, so the demo degrades to
"answers are generic" rather than "the app is broken".

It also lets the test suite exercise every service that calls a model without a
network, keeping the no-DB/no-network rule for pytest.
"""

from __future__ import annotations

import json

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

        # Practice generation.
        if "items" in props:
            return {"items": [{
                "prompt": "A 2 kg block slides at constant velocity across a rough floor. "
                          "What is the net force on it?",
                "kind": "mcq",
                "options": ["0 N", "6 N", "20 N", "24 N"],
                "correct_answer": "0 N",
                "problem_type": "net-force-constant-velocity",
            }]}

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
