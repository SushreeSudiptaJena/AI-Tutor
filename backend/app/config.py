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
ALIGNMENT_REFUSAL_THRESHOLD = float(_get("ALIGNMENT_REFUSAL_THRESHOLD", "0.35"))

# --- languages (i18n-001) ---------------------------------------------------
LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "hi", "label": "हिन्दी"},
    {"code": "bn", "label": "বাংলা"},
    {"code": "ta", "label": "தமிழ்"},
    {"code": "te", "label": "తెలుగు"},
    {"code": "mr", "label": "मराठी"},
]
