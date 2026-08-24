"""FastAPI application.

Sync `def` endpoints only -- see the Async policy in CLAUDE.md.
Feature routers get included here as they land; today this is the baseline
required by infra-002.
"""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from . import config, db
from .routers import auth, student, tutor

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


_DEFAULT_CODES = {
    400: "bad_request", 401: "unauthenticated", 403: "forbidden",
    404: "not_found", 405: "bad_request", 409: "conflict", 503: "provider_unavailable",
}


@app.exception_handler(HTTPException)
def http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert FastAPI's {"detail": ...} into the contract's error envelope.

    Routes raise HTTPException(status, detail={"code": ..., "message": ...}) to
    control the code; a plain string detail still comes out well-formed.
    """
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code") or _DEFAULT_CODES.get(exc.status_code, "error")
        message = detail.get("message", "")
        extra = detail.get("detail", {})
    else:
        code = _DEFAULT_CODES.get(exc.status_code, "error")
        message = str(detail)
        extra = {}
    return error(code, message, exc.status_code, extra)


@app.exception_handler(RequestValidationError)
def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 with per-field messages, as the contract specifies."""
    fields: dict[str, str] = {}
    for err in exc.errors():
        # loc looks like ("body", "email"); the last string element is the field.
        name = next((p for p in reversed(err["loc"]) if isinstance(p, str)), "body")
        fields[name] = err.get("msg", "invalid")
    return error("validation_error", "Some fields are invalid.", 422, fields)


@app.exception_handler(404)
def not_found(request: Request, exc: Exception) -> JSONResponse:
    """404s, whether the route is unknown or the resource is.

    Starlette gives a status-code handler precedence over the HTTPException
    handler above, so this one sees *every* 404 -- including the ones routes
    raise deliberately with their own message. It used to answer all of them
    with "No such route.", which told a frontend the endpoint did not exist
    when in fact the gap id did not belong to that student.

    A route's own message wins; the generic one is only for a genuinely
    unmatched path.
    """
    if isinstance(exc, HTTPException) and isinstance(exc.detail, dict):
        return http_exception(request, exc)
    return error("not_found", "No such route.", 404)


@app.get("/health")
def health() -> dict:
    """Liveness. Always 200 if the process is up; reports the DB separately so a
    dropped database does not look like a dead app."""
    ok, note = db.ping()
    return {"status": "ok" if ok else "degraded", "db": "ok" if ok else note}


@app.get("/meta/provider-status")
def provider_status() -> dict:
    """Lets the demo show on screen which provider is live, what the fallback
    chain is, and how warm the cache is."""
    from .providers import cache as llm_cache, chain_names

    return {
        "active": config.PROVIDER,
        "fallbacks_available": config.configured_fallbacks(),
        "cache_enabled": config.LLM_CACHE_ENABLED,
        "chain": chain_names(),
        "cache": llm_cache.stats(),
    }


@app.get("/languages")
def languages() -> dict:
    return {"items": config.LANGUAGES}


# --- routers ----------------------------------------------------------------
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(tutor.router)
