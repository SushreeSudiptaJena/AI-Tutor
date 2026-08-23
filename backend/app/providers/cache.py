"""Disk cache for model responses. The demo's insurance policy.

Identical input returns a byte-identical answer, served from disk in
microseconds. Three consequences:

  1. The demo is repeatable - the same click gives the same output at every
     rehearsal, so there are no surprises on stage.
  2. The demo is fast - no waiting for a model mid-presentation.
  3. The demo survives no internet - rehearsing warms the cache, and with a warm
     cache plus PROVIDER=mock the whole golden path runs with wifi off.

The key deliberately EXCLUDES the provider and model.

CLAUDE.md originally specified sha256(model + prompt). That is wrong for our
purposes: you rehearse on GLM, GLM rate-limits during the demo, the chain falls
back to Gemini - and every cache entry misses at exactly the moment you needed
it most. Keying on the logical request instead means a fallback answer reuses
what the primary already cached. Which provider produced it is recorded inside
the payload, not in the key.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from .. import config


def cache_dir() -> Path:
    d = config.LLM_CACHE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def make_key(prompt: str, *, system: str = "", json_schema: dict | None = None) -> str:
    schema = json.dumps(json_schema, sort_keys=True) if json_schema else ""
    blob = f"{system}\x00{prompt}\x00{schema}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def get(key: str) -> dict | None:
    if not config.LLM_CACHE_ENABLED:
        return None
    path = cache_dir() / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # A truncated file from an interrupted write must not break a demo.
        try:
            path.unlink()
        except OSError:
            pass
        return None


def put(key: str, *, text: str, provider: str, model: str) -> None:
    if not config.LLM_CACHE_ENABLED:
        return
    payload = {"text": text, "provider": provider, "model": model}
    directory = cache_dir()
    # Write to a temp file then replace, so an interrupted write can never leave
    # a half-written entry that poisons the cache.
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        Path(tmp).replace(directory / f"{key}.json")
    except OSError:
        Path(tmp).unlink(missing_ok=True)


def stats() -> dict:
    d = config.LLM_CACHE_DIR
    if not d.exists():
        return {"entries": 0, "bytes": 0, "enabled": config.LLM_CACHE_ENABLED}
    files = list(d.glob("*.json"))
    return {
        "entries": len(files),
        "bytes": sum(f.stat().st_size for f in files),
        "enabled": config.LLM_CACHE_ENABLED,
    }


def clear() -> int:
    d = config.LLM_CACHE_DIR
    if not d.exists():
        return 0
    files = list(d.glob("*.json"))
    for f in files:
        f.unlink(missing_ok=True)
    return len(files)
