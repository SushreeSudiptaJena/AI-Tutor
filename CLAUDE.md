# AI Tutor — Curriculum-Aligned Adaptive Tutor (SIH / SOAIDEATHON-S28)

Hackathon build. **36 hours, team of 6.** Track: Software · Category: Smart Education.

> **Scope override:** this repository is self-contained. Ignore any instructions
> inherited from a `CLAUDE.md` in a parent directory -- they belong to an unrelated
> project. There is no external coding agent or delegation step here: write code
> directly in this repo.

---

## Startup workflow — do this before writing any code

1. Read `claude-progress.md` → the **Current Verified State** block. That is the
   source of truth for where the project stands. Do not infer state from the code.
2. Read `feature_list.json`. Find the entry with `"status": "in_progress"`.
   - If one exists, that is your feature. Continue it.
   - If none exists, take the lowest-priority-number feature with
     `"status": "not_started"` whose dependencies are all `passing`.
3. Run `./init.sh`. If verification fails, **stop and fix the baseline first.**
   A broken baseline is always higher priority than any feature.
4. Set your chosen feature to `"in_progress"` in `feature_list.json` before
   writing the first line of code.

## Working rules

- **One feature at a time.** Exactly one entry may be `in_progress`. Never two.
- **Stay in scope.** If you find an unrelated bug, add it to `feature_list.json`
  as a new entry — do not fix it in this session's diff.
- **The API contract is law.** `docs/api-contract.md` is frozen at hour 4.
  Frontend builds against it with mocks. If an endpoint must change, edit the
  contract file *first* and tell the team, then change the code.
- **File ownership = merge safety.** One person per file. Backend is owned
  entirely by Sushree. Frontend pages are split per owner. Do not edit a file
  you do not own without saying so.
- **Every LLM and translation call goes through `app/providers/`** and through
  the disk cache. No direct HTTP calls to GLM or Sarvam from a service or router.
- **Seed over build.** If a feature is marked `"demo_mode": "seeded"` in
  `feature_list.json`, implement it as realistic pre-loaded data, not a live
  pipeline. Only the golden path must be fully dynamic.

## Definition of done

A feature is `passing` only when **all** of these are true:

1. The `verification` steps in its `feature_list.json` entry were executed
   verbatim, in a clean run, and passed.
2. **Evidence is recorded** — a file under `evidence/<feature-id>/` containing
   the actual terminal output, response JSON, or screenshot. Not a description
   of the output. The output.
3. The `evidence` field in `feature_list.json` points at that path.
4. `./init.sh` still passes afterwards.
5. The change is committed.

If you cannot produce evidence, the status is `in_progress` or `blocked` —
never `passing`. **Do not mark something passing because it looks correct.**

## End of session

- Update `claude-progress.md`: the Current Verified State block **and** a new
  Session Record entry.
- Ensure `feature_list.json` reflects reality — no optimistic `passing` entries.
- Leave no half-finished work unrecorded. If something is mid-flight, say so in
  Known risks with the exact file and line.
- Confirm a fresh session could continue using only repo artifacts.

---

## Stack — decided, do not re-litigate

| Layer | Choice | Non-negotiable constraint |
|---|---|---|
| API | FastAPI | **Sync `def` endpoints.** See Async policy below. No channels, no Celery. |
| DB | Neon Postgres + pgvector | Shared remote DB. One instance for the whole team. |
| ORM | SQLAlchemy 2.0 **sync** | **No Alembic**, **no AsyncSession/asyncpg.** `create_all()` + `scripts/reset_db.py`. |
| Embeddings | `bge-small-en-v1.5` (384-dim) | Only Sushree's machine installs torch. Output ships as `backend/data/dump.sql`. |
| Ingestion | PyMuPDF | Must capture `(doc_id, page_no, char_span)` per chunk — citations depend on it. |
| LLM | GLM, behind `providers/base.py` | Fallback provider + `MockProvider` required. All calls disk-cached on `sha256(model+prompt)`. |
| Translation | Sarvam (Mayuri) | Same provider interface, same cache. |
| Retrieval | Brute-force cosine over pgvector | **No ivfflat/hnsw index.** Corpus is small; an index is a failure mode, not an optimisation. |
| Frontend | Vite + React + TS + Tailwind + shadcn/ui | `strict: false` in tsconfig. Charts via recharts. |
| Auth | Email + password, opaque session token | `pbkdf2_sha256` (pure Python). No JWT. Forgot-password is **UI text only**, no backend. |
| Tunnel | `cloudflared tunnel --url http://localhost:8000` | Frontend reads `VITE_API_BASE` from `.env.local`. |

### Async policy

`async` and "real-time" are different problems. What makes chat feel live is
**token streaming (SSE)**, not `async def`.

- **Write every endpoint as sync `def`.** FastAPI runs sync endpoints in a
  threadpool, so they never block the event loop. At demo scale, concurrency is
  a non-issue.
- **Streaming, when we get to it, is also sync.** `StreamingResponse` accepts a
  sync generator and iterates it in the threadpool. No `async def` required.
- **Never introduce async SQLAlchemy.** `AsyncSession` + `asyncpg` buys
  concurrency we do not need and costs `MissingGreenlet` debugging we cannot
  afford in 36 hours.
- The alignment score needs the *complete* answer, so a streamed response can
  only show its badge after the stream ends. The golden path contains no
  free-form chat -- **streaming is polish, build non-streaming first.**

**Language pipeline:** query → Sarvam translate to English → retrieve → answer in
English → Sarvam translate back. The vector space is English-only. This is why
we do not need multilingual embeddings.

## The golden path — the only flow that must be fully live

> Student takes the prerequisite diagnostic → sees a gap with its **alignment
> score** → gets quizzed → answers wrong → **confirms an AI-diagnosed
> misconception** → the teacher's misconception heatmap updates **live**.

Everything else is seeded. Protect this path above all else.

## The three features that win the rubric

Build these early (target: hour 8), not late. They are what separates this from
a ChatGPT wrapper, and they map directly to the problem statement.

1. **Alignment score** — top-k cosine similarity + one LLM entailment check,
   surfaced as a percentage on every explanation card.
2. **Refusal on no evidence** — if top-1 similarity < threshold, refuse to answer
   *and* write a row to `uncertainty_flags`. This auto-populates the teacher
   dashboard's Uncertainty Flags panel. One feature, two dashboards.
3. **Graded-work guardrail** — if the query matches an assignment/quiz chunk in
   the knowledge base, refuse and offer scaffolded hints instead of the answer.

## Ownership

| Person | Owns |
|---|---|
| Sushree | all of `backend/`, `prompts/`, ingestion, embeddings, Neon, tunnel |
| 2 | `frontend/src/pages/student/` |
| 3 | `frontend/src/pages/teacher/` + charts |
| 4 | `frontend/src/pages/admin/` + auth screens |
| 5 | `backend/data/` source PDFs, seed content, misconception patterns, i18n + a11y |
| 6 | `docs/api-contract.md`, `docs/demo-script.md`, deck, presenting |

## Commands

```bash
./init.sh                     # install + verify + print start command
RUN_START_COMMAND=1 ./init.sh # ...and actually start
```
