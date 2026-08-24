"""Settings, read once from the repo-root .env.

Deliberately plain os.getenv -- no settings framework. Everything here is a
string or a simple cast, and a missing value should fail loudly at the point of
use, not at import time (so tests and `--help` still work without a database).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# --- database ---------------------------------------------------------------
DATABASE_URL_RAW = _get("DATABASE_URL")


def database_url() -> str:
    """SQLAlchemy URL. Providers hand out postgresql://; we drive it with psycopg 3."""
    url = DATABASE_URL_RAW
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and paste the "
            "connection string from the team channel."
        )
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


# --- providers --------------------------------------------------------------
PROVIDER = _get("PROVIDER", "glm")

GLM_API_KEY = _get("GLM_API_KEY")
GLM_MODEL = _get("GLM_MODEL", "glm-4-flash")

FALLBACK_API_KEY_GEMINI = _get("FALLBACK_API_KEY_GEMINI")
FALLBACK_MODEL_GEMINI = _get("FALLBACK_MODEL_GEMINI")
FALLBACK_API_KEY_GROQ = _get("FALLBACK_API_KEY_GROQ")
FALLBACK_MODEL_GROQ = _get("FALLBACK_MODEL_GROQ")
FALLBACK_MODEL_GROQ_ALTERNATIVE = _get("FALLBACK_MODEL_GROQ_ALTERNATIVE")

SARVAM_API_KEY = _get("SARVAM_API_KEY")

LLM_CACHE_ENABLED = _get("LLM_CACHE_ENABLED", "1") == "1"
LLM_CACHE_DIR = REPO_ROOT / "backend" / ".cache"


def configured_fallbacks() -> list[str]:
    """Which fallback vendors actually have a key. Surfaced by /meta/provider-status."""
    out = []
    if FALLBACK_API_KEY_GEMINI and FALLBACK_MODEL_GEMINI:
        out.append("gemini")
    if FALLBACK_API_KEY_GROQ and FALLBACK_MODEL_GROQ:
        out.append("groq")
    return out


# --- retrieval --------------------------------------------------------------
EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# NOT a round guess, and NOT a low-and-safe default. bge-small has a high
# similarity floor: unrelated text still scores 0.50-0.68 against our corpus, so
# at the original 0.35 the refusal in rag-003 would never once have fired, and
# nobody would have noticed -- "it answered" looks exactly like success.
#
# Measured on the CS-C corpus (evidence/rag-002/threshold-calibration-cs-c.txt):
# lowest covered 0.7442, highest off-topic 0.7014. calibrate_threshold.py
# suggests 0.72; we run 0.70 deliberately, because the two gates fail in
# different directions. A similarity-gate refusal is final -- the student is
# told there is no material when there is -- whereas a question that slips past
# similarity still has to satisfy the entailment check, which caught the
# near-domain cases live (Rust at 0.7014 scored 0.0 entailment and was refused).
# So the threshold sits with headroom under the weakest covered question rather
# than tight against it.
#
# This value is a property of the ingested books. Re-measure after every ingest.
ALIGNMENT_REFUSAL_THRESHOLD = float(_get("ALIGNMENT_REFUSAL_THRESHOLD", "0.70"))

# --- languages (i18n-001) ---------------------------------------------------
LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "hi", "label": "हिन्दी"},
    {"code": "bn", "label": "বাংলা"},
    {"code": "ta", "label": "தமிழ்"},
    {"code": "te", "label": "తెలుగు"},
    {"code": "mr", "label": "मराठी"},
]
