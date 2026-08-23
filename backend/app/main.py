"""FastAPI application.

Sync `def` endpoints only -- see the Async policy in CLAUDE.md.
Feature routers get included here as they land; today this is the baseline
required by infra-002.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from . import config, db

app = FastAPI(
    title="AI Tutor",
    description="Curriculum-aligned adaptive tutor. See docs/api-contract.md.",
    version="0.1.0",
)

# The team is remote: the frontend runs on a teammate's laptop against a
# cloudflared tunnel, so we allow vite dev origins and *.trycloudflare.com.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    r"|^https://[a-z0-9-]+\.trycloudflare\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def error(code: str, message: str, status: int, detail: dict | None = None) -> JSONResponse:
    """The single error envelope from docs/api-contract.md."""
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "detail": detail or {}}},
    )


@app.exception_handler(404)
def not_found(request: Request, exc: Exception) -> JSONResponse:
    return error("not_found", "No such route.", 404)


@app.get("/health")
def health() -> dict:
    """Liveness. Always 200 if the process is up; reports the DB separately so a
    dropped database does not look like a dead app."""
    ok, note = db.ping()
    return {"status": "ok" if ok else "degraded", "db": "ok" if ok else note}


@app.get("/meta/provider-status")
def provider_status() -> dict:
    """Lets the demo show on screen which provider is live and that the cache is on."""
    return {
        "active": config.PROVIDER,
        "fallbacks_available": config.configured_fallbacks(),
        "cache_enabled": config.LLM_CACHE_ENABLED,
    }


@app.get("/languages")
def languages() -> dict:
    return {"items": config.LANGUAGES}
