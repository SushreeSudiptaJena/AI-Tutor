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

# SUBJECT-NEUTRAL ON PURPOSE. These used to be Newton's-laws text, left over
# from when the demo course was physics, and offline that was actively
# dangerous: an unrehearsed question under PROVIDER=mock came back with
# "draw a free-body diagram... apply F_net = m a" while the response claimed
# 80% alignment and carried five real citations to a DJANGO textbook. Confident
# prose about the wrong subject, wearing the right sources.
#
# A mock answer must never assert subject matter it cannot possibly know. It
# says what it IS instead, so a demo running on it is obvious rather than
# quietly wrong.
_EXPLANATION = (
    "[offline placeholder] This response came from the mock provider, so it is "
    "not a real answer to this question -- the model was not reachable and this "
    "exact question has not been asked before, so there was nothing cached to "
    "replay. The citations shown alongside it ARE real: they come from the "
    "approved course material by vector search, which needs no network. Ask "
    "this question once while online and it will be cached and answer properly."
)

_HINTS = [
    "[offline placeholder] Re-read the question and name exactly what is being asked for.",
    "[offline placeholder] Find the passage in the cited material that covers it.",
    "[offline placeholder] Write down what you already know before looking for what you do not.",
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
            # The distractor must name a misconception that EXISTS in the
            # seeded set, or a wrong answer produces silence -- the demo's
            # weakest moment. This one used to be a physics item mapped to
            # `velocity-implies-force`, which no longer exists anywhere, so
            # offline the wrong answer was diagnosed as nothing at all.
            return {"items": [{
                "prompt": "A form on a page creates a new blog post when submitted. "
                          "Which HTTP method should it use?",
                "kind": "mcq",
                "options": [
                    "POST, because the request changes server state",
                    "GET, because it is a simpler request",
                    "Either one; the method makes no difference",
                    "PUT, because a post is being written",
                ],
                "correct_answer": "POST, because the request changes server state",
                "problem_type": "http-method-choice",
                "distractors": {"GET, because it is a simpler request":
                                "get-for-state-change"},
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
