"""Where the seconds in one click actually go.

    .venv/Scripts/python.exe backend/scripts/profile_click.py

Splits each endpoint's wall clock into database round trips, embedding, model
calls and everything else, so "it feels slow" can be answered with which part.

Mutates demo state (submits the diagnostic, generates practice). Run
reset_demo_state.py afterwards.
"""

from __future__ import annotations

import sys
import time

sys.path.insert(0, "backend")

from sqlalchemy import event  # noqa: E402

from app import providers  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.services import embed as embed_mod  # noqa: E402

T = {"db": 0.0, "db_n": 0, "llm": 0.0, "llm_n": 0, "cached_n": 0,
     "embed": 0.0, "embed_n": 0}


def reset():
    for k in T:
        T[k] = 0 if isinstance(T[k], int) else 0.0


engine = get_engine()


@event.listens_for(engine, "before_cursor_execute")
def _b(conn, cur, st, p, ctx, em):
    ctx._t0 = time.time()


@event.listens_for(engine, "after_cursor_execute")
def _a(conn, cur, st, p, ctx, em):
    T["db"] += time.time() - ctx._t0
    T["db_n"] += 1


_real_complete = providers.complete


def _timed_complete(*a, **kw):
    t = time.time()
    out = _real_complete(*a, **kw)
    T["llm"] += time.time() - t
    T["llm_n"] += 1
    if getattr(out, "cached", False):
        T["cached_n"] += 1
    return out


providers.complete = _timed_complete
for mod_name in ("tutor", "evidence", "practice", "guardrail", "reteach", "syllabus"):
    try:
        mod = __import__(f"app.services.{mod_name}", fromlist=["x"])
        if hasattr(mod, "complete"):
            mod.complete = _timed_complete
    except ImportError:
        pass

_real_embed = embed_mod.embed_query


def _timed_embed(q):
    t = time.time()
    out = _real_embed(q)
    T["embed"] += time.time() - t
    T["embed_n"] += 1
    return out


embed_mod.embed_query = _timed_embed
for mod_name in ("retrieval", "guardrail"):
    mod = __import__(f"app.services.{mod_name}", fromlist=["x"])
    if hasattr(mod, "embed_query"):
        mod.embed_query = _timed_embed

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

c = TestClient(app)
tok = c.post("/auth/login",
             json={"email": "asha@example.edu", "password": "demo1234"}).json()["token"]
H = {"Authorization": "Bearer " + tok}

print(f"{'click':<34}{'wall':>7}{'db':>8}{'q':>4}{'model':>8}{'n':>3}"
      f"{'embed':>7}{'other':>8}")
print("-" * 79)


def run(label, fn):
    reset()
    t = time.time()
    r = fn()
    wall = time.time() - t
    other = wall - T["db"] - T["llm"] - T["embed"]
    cached = f"({T['cached_n']}c)" if T["cached_n"] else ""
    print(f"{label:<34}{wall:>6.2f}s{T['db']:>7.2f}s{T['db_n']:>4}"
          f"{T['llm']:>7.2f}s{T['llm_n']:>3}{T['embed']:>6.2f}s{other:>7.2f}s {cached}")
    return r


run("GET /student/course-summary", lambda: c.get("/student/course-summary", headers=H))
diag = run("GET /student/diagnostic", lambda: c.get("/student/diagnostic", headers=H)).json()

item = next(i for i in diag["items"] if i["concept"].startswith("HTTP methods"))
wrong = next(o for o in item["options"] if o.startswith("GET, because"))
sub = run("POST .../diagnostic/submit", lambda: c.post(
    f"/student/diagnostic/{diag['diagnostic_id']}/submit", headers=H,
    json={"answers": [{"item_id": item["id"], "answer": wrong}]})).json()

gap = next(g for g in sub["gaps"] if g["concept"].startswith("HTTP methods"))
run("GET /student/gaps", lambda: c.get("/student/gaps", headers=H))
run("GET .../gaps/{id}/lesson  [LLM]",
    lambda: c.get(f"/student/gaps/{gap['id']}/lesson", headers=H))
run("GET .../lesson again (cached)",
    lambda: c.get(f"/student/gaps/{gap['id']}/lesson", headers=H))
ps = run("POST /practice/generate  [LLM]", lambda: c.post(
    "/student/practice/generate", headers=H, json={"gap_id": gap["id"]})).json()
run("GET /student/practice/{id}",
    lambda: c.get(f"/student/practice/{ps['practice_set_id']}", headers=H))
run("POST /practice/answer  [LLM]", lambda: c.post(
    f"/student/practice/{ps['practice_set_id']}/answer", headers=H,
    json={"item_id": ps["items"][0]["id"], "answer": "GET"}))

print()
print("db    = time inside SQL round trips to Neon (q = how many)")
print("model = time waiting on the LLM provider (n = calls, Nc = served from disk cache)")
print("other = FastAPI, serialisation, python. Should be small.")
