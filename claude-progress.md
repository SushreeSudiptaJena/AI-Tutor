# claude-progress.md

Every session **reads this first** and **writes to it last**.

---

## Current Verified State

*Single source of truth for where the project stands. Update at end of every session.*

| Field | Value |
|---|---|
| **Repository root** | the directory containing this file (every path in this repo is relative to it) |
| **Standard startup path** | `./init.sh` (then `RUN_START_COMMAND=1 ./init.sh` to launch backend) |
| **Standard verification path** | `python -m pytest backend/tests -q && npm --prefix frontend run build` |
| **Highest priority unfinished feature** | `rag-004` — graded-work guardrail. `retrieval.search_assignments()` already exists for its cheap first half. |
| **Current blocker** | None for new work. `infra-001` and `infra-003` each need a second person to finish verifying; neither blocks anything downstream. |
| **Golden path status** | Retrieval spine live end to end. `rag-002` (alignment score) is done and answering over HTTP; `student-002/003/005/006` and `teacher-001` are still to build. |
| **Last verified** | 2026-08-24 — 96 tests pass, `./init.sh` green. Live: 1240 chunks of real course material ingested, retrieval + alignment + refusal verified through `POST /tutor/ask`. |

### Environment facts

- **DB:** Neon Postgres (shared, remote). One instance for the whole team. Connection string in `.env` as `DATABASE_URL`.
- **Two courses now share the database.** `PH101` (Mechanics) holds the stand-in physics corpus; `CS-C` (Programming with C) holds the real ingested textbook. **Every retrieval is course-scoped and `course_id` is a required argument** — an unscoped search returns a real citation from the wrong subject, which reads as a slightly odd answer rather than as a bug.
- **Source books are gitignored** (`backend/data/pdfs/*`), and rightly so: they are large and someone else's copyright. `manifest.json` is committed so the team can see what the corpus is made of. A teammate who needs the corpus consumes the shared Neon rows.
- **`ALIGNMENT_REFUSAL_THRESHOLD` is corpus-specific**, currently `0.70`, measured against the C book. Re-run `backend/scripts/calibrate_threshold.py` after any ingest.
- **Backend host:** Sushree's laptop, exposed via `cloudflared tunnel --url http://localhost:8000`. Tunnel URL changes on restart — post it to the team channel each time.
- **Frontend:** each teammate runs `npm run dev` locally with `VITE_API_BASE` in `frontend/.env.local` pointing at the current tunnel URL.
- **Keys:** GLM and Sarvam API keys confirmed working as of 2026-08-23.
- **Embeddings:** only Sushree's machine has torch/`bge-small-en-v1.5`. Everyone else consumes the shared Neon DB.

---

## Session Record

*Newest entry at the top. One entry per session.*

### Session 007 — 2026-08-24 — ingest-001, rag-001, rag-002, rag-003 PASSING

| | |
|---|---|
| **Goal** | Build the ingestion pipeline so it is ready the moment PDFs land, then the retrieval, evidence and refusal services on top of it. |
| **Completed** | `services/ingest.py` (PyMuPDF, page-anchored slicing, EPUB→fixed-PDF layout, self-verification), `scripts/ingest_pdfs.py`, `services/retrieval.py`, `services/evidence.py`, `services/tutor.py`, `routers/tutor.py` (`POST /tutor/ask`), `app/prompts.py` + `prompts/{evidence_entailment,tutor_answer}.md`, `backend/data/calibration/cs-c.json`, and a rewritten `calibrate_threshold.py` that is course-scoped and takes a question file. 54 new tests (42 → 96). |
| **Verification run** | Real course material supplied by the owner and ingested for real: *Practical C Programming* (Harwani, Packt 2020), 5th-sem CSE core reading — 645 pages, 636 with text, **1240 chunks** under a new course `CS-C`. Five randomly sampled chunks re-verified against the PDF two independent ways. Live retrieval, alignment scoring and refusal exercised against the real provider chain, then again over HTTP through `POST /tutor/ask` as a signed-in student (401 unauthenticated, 200 answered, 200 insufficient_evidence). |
| **Evidence recorded** | `evidence/ingest-001/verification.txt`, `evidence/rag-001/retrieval-live-cs-c.txt`, `evidence/rag-002/{alignment-live-cs-c,threshold-calibration-cs-c}.txt`, `evidence/rag-003/refusal-live-cs-c.txt` |
| **Commits** | Two: `ingest-001`, then the `rag-001` → `rag-003` chain. The three rag features are one code path with one test module, so splitting them further would have meant commits that could not pass their own tests. |
| **Known risks** | **The corpus is now C programming, not physics.** All seeded concepts, misconceptions, diagnostic and practice items are still Newton's laws under `PH101`, so the golden path demo and the ingested book are about different subjects. Someone has to decide which subject the demo runs on — if it is C, the content lead must redo `concepts/misconceptions/practice/diagnostic.json`; if it stays physics, `CS-C` is simply a second course that proves ingestion works. Nothing is broken either way, because retrieval is course-scoped. Secondary: cited page numbers for the C book come from our A4/11pt EPUB rendering, not the printed book — fine for "Show Source", wrong if anyone checks a physical copy. Embedding 1240 chunks takes ~15 minutes on this laptop; budget for that before re-ingesting on demo day. |
| **Next best action** | `rag-004` — the graded-work guardrail. `retrieval.search_assignments()` is already the door it knocks on, and the mock provider already answers an `intent` schema. It needs assignment material in `CS-C` to match against; there is none yet, only the seeded physics problem set under `PH101`. |

### Session 006 — 2026-08-23 — infra-004 PASSING

| | |
|---|---|
| **Goal** | Provider interface, disk cache, fallback chain, mock. |
| **Completed** | `providers/{base,cache,mock,http_providers,translate_sarvam}.py` and `__init__.complete()`. `scripts/bench_providers.py`. `/meta/provider-status` now exposes the chain and cache warmth. Contract updated. |
| **Verification run** | 42 pytest tests (no network). Live: cache hit 168x faster and byte-identical; primary key broken → different vendor answered; `PROVIDER=mock` with all keys blanked completed the golden path including the guardrail intent check; a warm cache answered with no working key at all. |
| **Evidence recorded** | `evidence/infra-004/verification.txt` |
| **Commits** | One. |
| **Known risks** | **GLM has no account balance** — paid models return 429 code 1113; only `glm-4.5-flash` works, at ~21.7s. It is third in the chain and must never lead. Gemini and Groq free tiers are the real capacity; watch for rate limits during heavy rehearsal. |
| **Next best action** | `ingest-001` — PyMuPDF over real PDFs. Blocked on the content lead supplying material; until then `corpus.json` stands in and everything downstream is testable. |

### Session 005 — 2026-08-23 — models, seed, auth-001 PASSING

| | |
|---|---|
| **Goal** | Build the data layer and authentication. |
| **Completed** | `models.py` (21 tables, live on Neon). `reset_db.py`. Eight content-lead JSON files in `backend/data/seed/` with validation that refuses to seed undiagnosable practice items. `seed.py` (idempotent, verified across three runs). `services/embed.py` (fastembed + BGE query prefix). `security.py`, `schemas.py`, `deps.py`, `routers/auth.py`, and the contract's error envelope wired into `main.py` for HTTPException and validation errors. |
| **Verification run** | 26 pytest tests, no DB and no network. Live retrieval: covered 0.834, off-syllabus 0.669, homework 0.925, conceptual-on-same-assignment 0.693. Live auth: 10-step round trip including wrong password, missing token, duplicate email, logout invalidation, and inspection of the stored hash. |
| **Evidence recorded** | `evidence/rag-001/retrieval-live.txt`, `evidence/auth-001/live-verification.txt`, `evidence/infra-001/schema-created.txt` |
| **Commits** | Three: models, seed, auth. |
| **Known risks** | The off-syllabus retrieval margin is thin — 0.669 against a 0.68 threshold. Once real PDFs are ingested the corpus shifts and this could invert; re-run `calibrate_threshold.py` after ingestion and do not trim the entailment call. `infra-001` and `infra-003` still need a second person. |
| **Next best action** | `infra-004` — provider interface with disk cache, GLM/Gemini/Groq fallbacks and MockProvider. Must land before anything calls an LLM, or the cache never gets retrofitted. |

### Session 004 — 2026-08-23 — infra-002 PASSING

| | |
|---|---|
| **Goal** | Get `./init.sh` green so the "fix the baseline first" rule becomes enforceable. |
| **Completed** | `backend/app/{config,db,main}.py` — sync FastAPI, lazy engine so the app imports without a DB. `/health`, `/meta/provider-status`, `/languages`, and the contract's 404 error envelope. `pytest.ini` + 4 baseline tests that need no DB and no network. Full Vite + React + TS + Tailwind v4 frontend that builds. `frontend/src/lib/api.ts` with the contract's types, including `TutorResponse` as a discriminated union. `.gitattributes` LF enforcement. |
| **Verification run** | Both steps verbatim. (1) Clean clone into a scratch dir with only `.env` copied: fresh venv, fresh `node_modules`, `./init.sh` exit 0, "Verification passed." (2) `RUN_START_COMMAND=1 ./init.sh` booted uvicorn; `GET /health` → 200 `{"status":"ok","db":"ok"}`. |
| **Evidence recorded** | `evidence/infra-002/verification.txt` |
| **Commits** | Squashed into one `infra-002` commit. |
| **Known risks** | `pgvector` and `PyMuPDF` are not in `requirements.txt` yet — they arrive with `ingest-001`, and PyMuPDF is the one most likely to need a wheel fallback. The `/health` DB check hits the network on every call; if the free tier throttles, add a short cache. |
| **Next best action** | `infra-004` — provider interface with disk cache, Gemini/Groq fallbacks, and `MockProvider`. It has no dependency on the blocked features and is the demo's insurance policy. |

### Session 003 — 2026-08-23 — infra-003 API contract

| | |
|---|---|
| **Goal** | Write the complete API contract and a README, then commit the scaffold. |
| **Completed** | `docs/api-contract.md` covering all 32 features across 46 endpoints — conventions, error envelope, shared objects (`User`, `Citation`, `EvidenceReport`, `Gap`, `TutorResponse`, `Misconception`, `PracticeItem`), and every admin/student/teacher/tutor route. `README.md` written. `infra-001` moved to `blocked` (correct status — it waits on another machine). |
| **Verification run** | Automated coverage check: 32/32 features referenced, 46 endpoints, all 7 golden-path features present. |
| **Evidence recorded** | `evidence/infra-003/contract-coverage.txt` |
| **Commits** | Initial scaffold commit. |
| **Known risks** | The contract is a *draft* until hour 4. `TutorResponse` is a discriminated union on `outcome` — if the frontend forgets to branch on it, refusals will render as blank answers. Flag this to whoever owns the student pages. |
| **Next best action** | `infra-002`: `frontend/package.json`, a minimal `backend/app/main.py` with `/health`, and one trivial pytest so `./init.sh` goes green. |

### Session 002 — 2026-08-23 — infra-001 (in progress)

| | |
|---|---|
| **Goal** | Stand up the shared Postgres + pgvector and prove the team can reach it. |
| **Completed** | `.venv` created and `init.sh` rewired to use it (no global installs). `backend/requirements.txt` seeded with the DB deps. `backend/scripts/check_db.py` written. `.env` created and confirmed gitignored; `.env.example` synced to the multi-fallback key names. Absolute paths and inherited parent-project instructions stripped from all tracked files. Async policy recorded in `CLAUDE.md`. |
| **Verification run** | `check_db.py --write` then `--read` from one machine. Connected to PostgreSQL 18.6, pgvector 0.8.6, `<->` distance operator returned a value. |
| **Evidence recorded** | `evidence/infra-001/two-machine-check.txt` — currently shows INCOMPLETE (1 machine). |
| **Commits** | *(none — nothing committed yet)* |
| **Known risks** | `infra-001` is NOT passing: one machine proves connectivity, not shareability. Provider fallbacks (Gemini + two Groq models) are configured in `.env` but no code reads them yet — that is `infra-004`. |
| **Next best action** | Get a teammate to run `check_db.py --write`, re-run `--read`, then flip `infra-001` to passing. In parallel start `infra-003` (the API contract) — it has no dependencies and five people are blocked on it. |

### Session 001 — 2026-08-23 — Scaffold

| | |
|---|---|
| **Goal** | Agree the stack, lay down the repo structure and the four harness files. |
| **Completed** | Folder skeleton (`backend/`, `frontend/`, `prompts/`, `docs/`, `evidence/`); `CLAUDE.md`, `init.sh`, `claude-progress.md`, `feature_list.json`. |
| **Verification run** | None — no runnable code yet. `init.sh` will fail until `backend/requirements.txt` and `frontend/package.json` exist (that is `infra-002`). |
| **Evidence recorded** | None. |
| **Commits** | *(pending — nothing committed yet)* |
| **Known risks** | `init.sh` is not yet green, so the "fix the baseline first" rule cannot be enforced until `infra-002` lands. Treat `infra-002` as the true first task. |
| **Next best action** | `infra-001` then `infra-002`: create the Neon project, write `backend/requirements.txt` + `frontend/package.json`, and get `./init.sh` to pass end to end. Then write `docs/api-contract.md` and freeze it — five people are blocked on that file. |

<!--
### Session NNN — YYYY-MM-DD — <short title>

| | |
|---|---|
| **Goal** | |
| **Completed** | |
| **Verification run** | |
| **Evidence recorded** | |
| **Commits** | |
| **Known risks** | |
| **Next best action** | |
-->
