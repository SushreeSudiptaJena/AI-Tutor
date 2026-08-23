# AI Tutor

A curriculum-aligned adaptive tutor. It teaches only from course material a verified admin has uploaded, shows the exact book and page behind every explanation, and says "I don't know" instead of guessing when the material doesn't cover something.

Built for **SIH / SOAIDEATHON-S28** — Track: Software · Category: Smart Education. Team of 6, 36 hours.

---

## The problem we're solving

> Develop an AI tutor that uses approved course content, identifies prerequisite gaps, generates adaptive explanations and practice, and cites the source material used. It must detect when it lacks evidence, avoid completing graded work on behalf of students, support multilingual and accessible interaction, and give teachers dashboards focused on misconceptions rather than surveillance.

Three things make this different from a chatbot with a textbook attached:

1. **Alignment score** — every explanation carries a percentage showing how directly it maps to approved syllabus material.
2. **It refuses when it has no evidence** — and that refusal is logged for the teacher instead of failing silently.
3. **It won't do graded work** — asked to solve an assignment question, it gives scaffolding, not the answer.

---

## Quick start

You need **Python 3.11+**, **Node 18+**, and the shared `DATABASE_URL` (ask in the team channel — it is never in git).

```bash
git clone <repo-url> && cd ai_tutor

cp .env.example .env          # then paste DATABASE_URL and the API keys into .env
./init.sh                     # creates .venv, installs everything, verifies
```

`init.sh` prints the three commands to start the app. Roughly:

```bash
cloudflared tunnel --url http://localhost:8000     # terminal 1 — backend owner only
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000 --app-dir backend
npm --prefix frontend run dev                      # terminal 3
```

> **On frontend only?** You don't need Python or a database. Put the backend owner's tunnel URL in `frontend/.env.local` as `VITE_API_BASE=https://...` and run `npm --prefix frontend run dev`.

If `init.sh` fails verification, **fix that before touching any feature.** A broken baseline outranks everything.

---

## How the team works

We're remote, so a few rules keep six people out of each other's way.

| Rule | Why |
|---|---|
| **One person per file.** Backend is owned by one person; frontend pages are split per owner. | Merge conflicts are the #1 way a hackathon dies. |
| **`docs/api-contract.md` is frozen at hour 4.** | Five people build against it with mocks while the backend catches up. Change the contract *before* the code. |
| **Only one feature `in_progress` at a time.** | Tracked in `feature_list.json`. |
| **Nothing is "done" without evidence.** | Real terminal output or a screenshot in `evidence/<feature-id>/`. Not a description of it. |
| **Seed over build.** | Only the golden path must be fully live. Everything else ships as realistic pre-loaded data. |

### The golden path

The one flow that must work live, end to end, on demo day:

> Student takes the prerequisite diagnostic → sees a gap with its **alignment score** → gets quizzed → answers wrong → **confirms the AI-diagnosed misconception** → the teacher's heatmap updates **live**.

Protect this above all else.

---

## Repo layout

```
CLAUDE.md              operating rules — read this first
claude-progress.md     where the project stands right now
feature_list.json      all 32 features, their status and how to verify each
init.sh                install + verify + print start command
pytest.ini             test config (pythonpath = backend)
.env.example           copy to .env, fill in (.env is gitignored)

docs/
  api-contract.md      every endpoint and response shape (frozen hour 4)
  demo-script.md       the golden path, written out for rehearsal

prompts/               LLM prompt templates as plain .md files
backend/
  app/main.py          FastAPI app: CORS, /health, /languages
  app/config.py        reads .env
  app/db.py            engine + session (sync)
  app/routers/         one file per dashboard
  app/services/        ingestion, retrieval, evidence check, guardrails
  app/providers/       LLM + translation behind one interface, with cache
  scripts/             check_db.py, seed.py, ingest_pdfs.py
  data/                source PDFs and the seeded dump
  tests/               baseline + feature tests
frontend/src/
  lib/api.ts           every fetch lives here, plus contract types
  pages/{admin,student,teacher}/
  components/ui/       shadcn components
evidence/              proof that features actually work
```

---

## Stack

| Layer | Choice |
|---|---|
| API | FastAPI — **sync `def` endpoints only** |
| Database | Postgres + pgvector (Neon free tier, shared by the team) |
| ORM | SQLAlchemy 2.0 sync — no Alembic, no async |
| Ingestion | PyMuPDF — captures page numbers so citations resolve |
| Embeddings | `bge-small-en-v1.5`, 384-dim |
| LLM | GLM, with Gemini and Groq fallbacks behind one interface |
| Translation | Sarvam |
| Frontend | Vite + React + TypeScript + Tailwind + shadcn/ui |
| Auth | Email + password, opaque session token, `pbkdf2_sha256` |

**Why sync, not async:** what makes chat feel live is token streaming (SSE), not `async def`. FastAPI runs sync endpoints in a threadpool and `StreamingResponse` accepts a sync generator, so we get streaming without async SQLAlchemy — and without the `MissingGreenlet` debugging that would cost us hours we don't have. Full reasoning in `CLAUDE.md`.

**Why the LLM cache:** every model call is cached to disk on `sha256(model + prompt)`. The demo replays instantly and identically, and survives venue wifi dying. Set `PROVIDER=mock` to run the whole golden path with no internet at all.

---

## Security notes

- `.env`, `.venv/` and the LLM cache are gitignored. **Never commit a connection string or an API key.**
- Share secrets in the team channel, not in the repo.
- Teacher dashboard responses are anonymized at the API level — no student id, name, or email in any payload.
