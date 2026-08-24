"""Prompts live in `prompts/*.md`, not in Python string literals.

Two reasons. They are edited far more often than the code around them, and a
prompt change should show up in `git diff` as a prose change rather than buried
in a service. And the content lead can read and improve them without touching
the backend.

Placeholders are `{{double_braced}}` and substituted literally -- deliberately
NOT `str.format()`. The retrieved context is course material, and this corpus is
a C programming book: `printf("{%d}", n)` in a passage would make `.format()`
raise KeyError on text we do not control.
"""

from __future__ import annotations

import re
from functools import lru_cache

from . import config

PROMPT_DIR = config.REPO_ROOT / "prompts"


@lru_cache(maxsize=32)
def load(name: str) -> str:
    path = PROMPT_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"No prompt named {name!r} in {PROMPT_DIR}")
    return path.read_text(encoding="utf-8").strip()


PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def render(name: str, **values: object) -> str:
    """Fill `{{placeholders}}`. A placeholder the caller did not supply is an
    error worth seeing rather than a literal `{{context}}` sent to a model.

    The template is checked BEFORE substitution, never after. Substituted values
    are course material, and this corpus is a C programming book: a nested array
    initializer -- `int a[2][2] = {{1,2},{3,4}};` -- contains `{{` and `}}`, and
    scanning the rendered text would read that as an unfilled placeholder and
    refuse to render a perfectly good prompt.
    """
    text = load(name)

    required = set(PLACEHOLDER.findall(text))
    missing = required - set(values)
    if missing:
        raise KeyError(f"prompt {name!r} needs {sorted(missing)}, which was not supplied")

    for key in required:
        text = text.replace("{{" + key + "}}", str(values[key]))
    return text
