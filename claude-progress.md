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
| **Highest priority unfinished feature** | `infra-002` — green baseline (`package.json`, `backend/tests`, `/health`). `infra-001` and `infra-003` both await a teammate. |
| **Current blocker** | Two features need a second person: `infra-001` (teammate runs `check_db.py --write`) and `infra-003` (teammate builds one page against the mock). Neither blocks new work. |
| **Golden path status** | Not started |
| **Last verified** | 2026-08-23 — DB reachable: PostgreSQL 18.6, pgvector 0.8.6, distance operator exercised. `init.sh` still not green (no `package.json` / `backend/tests`). |

### Environment facts

- **DB:** Neon Postgres (shared, remote). One instance for the whole team. Connection string in `.env` as `DATABASE_URL`.
- **Backend host:** Sushree's laptop, exposed via `cloudflared tunnel --url http://localhost:8000`. Tunnel URL changes on restart — post it to the team channel each time.
- **Frontend:** each teammate runs `npm run dev` locally with `VITE_API_BASE` in `frontend/.env.local` pointing at the current tunnel URL.
- **Keys:** GLM and Sarvam API keys confirmed working as of 2026-08-23.
- **Embeddings:** only Sushree's machine has torch/`bge-small-en-v1.5`. Everyone else consumes the shared Neon DB.

---

## Session Record

*Newest entry at the top. One entry per session.*

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
