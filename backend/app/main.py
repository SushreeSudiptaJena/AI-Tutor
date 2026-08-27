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
from .routers import admin, admin_batches, auth, student, teacher, tutor

app = FastAPI(
    title="AI Tutor",
    description="Curriculum-aligned adaptive tutor. See docs/api-contract.md.",
    version="0.1.0",
)

# The team is remote: the frontend runs on a teammate's laptop against a
# cloudflared tunnel, so we allow vite dev origins and *.trycloudflare.com.
#
# *.onrender.com is here for the deployed build. It is belt-and-braces rather
# than load-bearing -- Render serves the frontend from this same process, so
# those calls are same-origin and never preflight. It matters only if someone
# points a locally-run or separately-hosted frontend at the deployed API.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    r"|^https://[a-z0-9-]+\.trycloudflare\.com$"
    r"|^https://[a-z0-9-]+\.onrender\.com$",
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
app.include_router(admin.router)
app.include_router(admin_batches.router)
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(teacher.router)
app.include_router(tutor.router)


# --- the built frontend -----------------------------------------------------
# Deployed as ONE Render service: this process serves the API *and* the Vite
# build, so the browser talks to a single origin and there is no CORS hop and
# no second service to cold-start. Locally `npm run dev` still serves the
# frontend on :5173 and frontend/dist may not exist -- everything below is
# skipped in that case, so nothing here affects development or the test suite.
#
# Registered AFTER the routers on purpose. FastAPI matches routes in
# registration order, so every real endpoint above wins before the SPA
# catch-all at the bottom is ever considered.
FRONTEND_DIST = config.REPO_ROOT / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    _INDEX = FRONTEND_DIST / "index.html"

    # Hashed filenames (index-BpFiJM1E.js) -- Vite emits a new name whenever
    # the contents change, so these are safe to serve straight off disk.
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"),
              name="assets")

    @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
    def spa(full_path: str, request: Request) -> FileResponse | JSONResponse:
        """Serve the SPA shell for client-side routes.

        React Router owns /login, /dashboard, /admin, /admin/login and
        /teacher in the browser. A hard refresh or a pasted link sends that
        path to us first, and the shell has to come back so the router can
        take over.

        The split is on Accept, NOT on a path prefix. The frontend's routes
        and the API's genuinely overlap -- /admin and /teacher are both a
        router path and a router prefix -- so any prefix rule breaks one side
        or the other. What actually distinguishes them is who is asking: a
        browser navigating sends `Accept: text/html`, while every call from
        lib/api.ts is a fetch() that sends `Accept: */*`. So an unknown path
        answers HTML to a navigation and the contract's JSON 404 to a fetch,
        which is what each caller can handle.
        """
        # The root is never an API route, so it is always the app -- including
        # to a bare `curl /`, which sends Accept: */* and would otherwise get
        # the JSON 404 below and read as a broken static mount.
        if not full_path:
            return FileResponse(_INDEX)

        # A real file (favicon.ico, robots.txt) wins over the shell. The
        # is_relative_to guard keeps ../ out of the path.
        candidate = (FRONTEND_DIST / full_path).resolve()
        if candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST):
            return FileResponse(candidate)

        if "text/html" not in request.headers.get("accept", ""):
            return error("not_found", "No such route.", 404)

        return FileResponse(_INDEX)
