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
| **Highest priority unfinished feature** | **None in the backend.** Every backend feature is passing. What is left needs other people: `demo-001` needs a second operator and two laptops, `a11y-001` and `auth-002` need frontend pages that do not exist yet, and `infra-001/003/005` each need one teammate to confirm from another machine. |
| **Current blocker** | None for new work. `infra-001`, `infra-003` and `infra-005` each need a second person to finish verifying; none blocks anything downstream. |
| **Demo course** | **CSW2 — Computer Science Workshop 2 (Django).** Not physics. Every citation in the demo now opens a real page of a real ingested PDF. |
| **Golden path status** | **COMPLETE, and re-verified end to end on CSW2.** diagnostic → gap attributed to CSW1 → lesson with alignment score + page-anchored citations → generated practice → wrong answer → specific misconception → confirm → teacher heatmap increments; deny leaves it unchanged. |
| **Last verified** | 2026-08-25 — 319 tests pass, `./init.sh` green, `ingest_pdfs.py --verify` PASS with 0 failures across the whole corpus. **38 of 45 features passing; 6 blocked on other people, 1 (`ingest-003`) open and real.** |
| **Demo script** | `docs/demo-script.md` — written, and it is what `demo-001` runs. Rehearse the exact questions in it **while online**: the disk cache is what makes the offline fallback show real answers. |
| **Student surface is complete** | `student-001` … `student-009` all passing. The API contract has no unbuilt student endpoint left. `student-009` added answer read-back: `GET /student/diagnostic` carries `your_answer` + `submitted_at`, `GET /student/practice/{id}` replays a set with its answers and any pending misconception question, and `Gap` carries `latest_practice_set_id`. **A reload no longer wipes a student's answers.** |

### Environment facts

- **DB:** Neon Postgres (shared, remote). One instance for the whole team. Connection string in `.env` as `DATABASE_URL`.
- **Two courses now share the database.** `PH101` (Mechanics) holds the stand-in physics corpus; `CS-C` (Programming with C) holds the real ingested textbook. **Every retrieval is course-scoped and `course_id` is a required argument** — an unscoped search returns a real citation from the wrong subject, which reads as a slightly odd answer rather than as a bug.
- **Source books are gitignored** (`backend/data/pdfs/*`), and rightly so: they are large and someone else's copyright. `manifest.json` is committed so the team can see what the corpus is made of. A teammate who needs the corpus consumes the shared Neon rows.
- **`ALIGNMENT_REFUSAL_THRESHOLD` is corpus-specific**, currently `0.70`, now measured against BOTH books (`evidence/rag-002/threshold-calibration-{cs-c,csw2}.txt`). `calibrate_threshold.py` suggests 0.72 for each; **do not take that suggestion.** The `url-routing` concept tops out at 0.7274 similarity and is now a live diagnostic item, so 0.72 would leave it 0.0074 of headroom. Re-run the calibration after any ingest, and re-measure `url-routing` specifically.
- **Five courses now share the database.** `CSW2` Computer Science Workshop 2 — Django textbook + seven real assignment PDFs — **is the demo course**, and `CSW1` is its prerequisite (the course every gap is attributed to; it has no corpus and needs none). `CS-C` Programming with C is a second real ingested book. `PH101`/`PH000` are the retired physics stand-in: still present, still reachable, and harmless, because retrieval, the diagnostic and the heatmap are all course-scoped.
- **Two concepts are deliberately NOT diagnostic-testable.** `python-classes-objects` and `html-forms` fail the entailment half of the evidence check against the Django book (0.4591 and 0.4892) — it *uses* classes and forms on every page and never *teaches* them. They carry no `prerequisite_course`, so no diagnostic item tests them and no gap lesson is ever asked for them. They are not deleted, because `seed.py`'s `add_diagnoses()` silently skips a misconception whose `problem_type` has no practice item — deleting their practice items empties two heatmap rows with no error anywhere.
- **`seed.py` never deletes.** It upserts by natural key, so content removed from a seed file stays in the shared database as a phantom row. One such row (`model-fields`) was found via `GET /student/mastery` and deleted by hand; the code is still unfixed and tracked as `infra-006`. Anything that enumerates a whole course will surface these, so check before assuming the DB matches the seed files.
- **The mock provider must never assert subject matter.** It used to answer with Newton's-laws prose left over from the physics course, so with the wifi off an unrehearsed Django question came back with "draw a free-body diagram" at 80% alignment carrying five real Django citations. It now says `[offline placeholder]`. Anything seeded that is *subject-specific* is a demo-day hazard after a course change — check it, do not assume it.
- **Offline works because of the disk cache, not because the mock is good.** The cache is keyed on `sha256(model + prompt)`, so a rehearsed question replays its real answer with no network. An unrehearsed one falls through to the placeholder. **Rehearse the exact demo questions online first.**
- **`GET /` is a 404, and that is correct.** There is no root route; opening the bare tunnel URL in a browser returns `{"error":{"code":"not_found","message":"No such route."}}`. Use `/health` or `/docs` to check the backend is alive. This looks like a broken tunnel and is not one.
- **`diagnostic_responses` is new (`student-009`) and `reset_demo_state.py` clears it.** It stores the answer text a student picked and *deliberately no correctness column* — that is what keeps the no-score stance true at the database level, and two tests guard it. If you ever add a reset path, clear this table too: otherwise the demo opens with every option already selected from the last rehearsal.
- **Two re-runnable check scripts now exist.** `backend/scripts/smoke_golden_path.py` runs the whole golden path against a live backend and asserts the heatmap increments; `backend/scripts/verify_student_009.py` runs that feature's verification steps. Both mutate demo state — run `reset_demo_state.py` after.
- **The reteach panel starts with ONE unit after a reset. Press “draft top 3 + top 3” to fill it.** `POST /teacher/reteach/suggest-top` (`teacher-008`) drafts three from the misconception heatmap and three from the prerequisite gap map; it takes about a minute of model calls the first time and is free after that (disk cache). It is idempotent — pressing it again creates nothing and skips with reasons — so it is safe to run during a rehearsal. **Do it before the demo, not during it.**
- **The audit log hides `seed.run` by default** (`admin-004`), because every `reset_demo_state.py` run writes one and they had come to outnumber every real row. `?include_system=true` shows them.
- **`reset_demo_state.py` is the pre-demo cleanup**, not `reset_db.py`. It deletes only transactional rows (attempts, diagnoses, gaps, mastery, generated practice, flags) and re-seeds the class history. `reset_db.py` drops `chunks` too — 3,000+ embeddings, ~40 minutes to regenerate.
- **`cloudflared` is a standalone binary in `~/bin`**, not an installed service — the winget MSI needs elevation. `./tunnel.sh` starts it and prints the line to post to the team channel.
- **Watch for stale servers.** A uvicorn left running from an earlier session was holding port 8000 and serving pre-auth code; `/health` answered 200 while every real route 404'd. `./tunnel.sh` now refuses to tunnel to a dead port, but check the port owner if routes vanish. **This bit again on 2026-08-24** — three uvicorns from the previous day were still up on 8011/8012/8013, all competing for the same Neon database. Check for strays with `Get-NetTCPConnection -State Listen`, not just port 8000.
- **Hit `/health` once after starting the backend, before anyone clicks anything.** Opening a Neon connection costs ~3.5s; running a query on an open one costs ~0.12s. `db.py` now pre-warms `POOL_SIZE` connections in parallel on first use (~6s once), and `/health` is what triggers it. Skip this and the first student's first click pays the handshake. See `perf-001` and `evidence/perf-001/measurements.txt`.
- **Latency is the link, not the database, and not the code.** Measured with `EXPLAIN (ANALYZE, BUFFERS)`: the retrieval query — brute-force cosine over 3,261 chunks, no index — has an **execution time of 7.9 ms** server-side, every buffer a `shared hit`. The same query observed from this laptop takes ~320 ms, and a bare `SELECT 1` takes ~137 ms. **Effectively all of it is round-trip time to `ap-southeast-1`**, and a vector query costs extra because the 384-float parameter is ~6 KB of query text going up the wire. So a 5-query page has a floor of roughly a second here and would be ~50 ms with the API in the database's region. `perf-001` cut the number of round trips (`/student/diagnostic` 12 → 4) because that is the only lever this repo has. **Do not go looking for a slow query — there isn't one.**
- **Cold buffers cost seconds, and that is a demo hazard.** The same retrieval query measured 6.0s once with cold buffers and 0.3s warm. Warming the connection pool via `/health` is not enough on its own — **run `backend/scripts/smoke_golden_path.py` once before the demo** (then `reset_demo_state.py`) so the corpus pages are in the compute's cache, not just the connections open.
- **`backend/scripts/profile_click.py`** splits any click into database / model / embedding / other. Use it before believing anything about where time goes; it is what showed the LLM contributing 0.00s (disk cache) while the database carried the entire wall clock.
- **Backend host:** Sushree's laptop, exposed via `cloudflared tunnel --url http://localhost:8000`. Tunnel URL changes on restart — post it to the team channel each time.
- **Frontend:** each teammate runs `npm run dev` locally with `VITE_API_BASE` in `frontend/.env.local` pointing at the current tunnel URL.
- **Keys:** GLM and Sarvam API keys confirmed working as of 2026-08-23.
- **Embeddings:** only Sushree's machine has torch/`bge-small-en-v1.5`. Everyone else consumes the shared Neon DB.

---

## Session Record

*Newest entry at the top. One entry per session.*

### Session 015 — 2026-08-25 — DLD corpus, admin-005/006/007, and a verifier that was lying

| | |
|---|---|
| **Goal** | Seven things raised by the owner: strip docs from git (left to them), where archived material lives, an admin delete endpoint, a `reference` material kind, missing auth tests, why not GLM 5.3, and ingest a Digital Logic Design corpus. |
| **Completed** | `content-002` (DLD corpus), `admin-005` (semester / admission batches / term window), `admin-006` (guarded delete), `admin-007` (`reference` kind + .txt/.md/.docx ingestion), and `ingest-002` (verifier fix). 319 tests (was 310). Two migrations written and run. |
| **Verification run** | Each feature verified live with a re-runnable script; `ingest_pdfs.py --verify` now reports **PASS, 0 failures across 5,300+ chunks** where it previously reported 3. |
| **Evidence recorded** | `evidence/admin-005/`, `evidence/admin-006/`, `evidence/admin-007/`, `evidence/ingest-002/` |
| **Commits** | Four. |
| **What verifying found that reading would not have** | **A half-ingested textbook was answering live queries.** The first DLD ingest was interrupted; `retrieval` filters only on `Material.status == 'active'` and never looks at `ingest_status`, so 320 of 2053 chunks served page-anchored citations from a fraction of a book. Logged as `ingest-003`; the partial material was deleted by hand. **The citation verifier was itself wrong.** Three chunks were reported as claiming a page their text was not on — the chunks were correct. `squash()` did not fold a line-broken word the way `normalise()` does, so `"pre-
ceding"` vs `"preceding"` failed every chunk containing one. I logged that as invisible because all three were in assignments, which are never quoted; ingesting Roth produced a fourth **in a textbook**, which forced the real diagnosis instead of the assumed one. **The material-kinds list lived in four places** and adding `reference` to the model left the CLI rejecting it. **Upload accepted `.txt`/`.md` that the ingester refused**, so such a file was stored, pending, and un-ingestable forever. **`admin-005`'s date validation had a hole** before `admin-006` existed to fall in it: sending `term_end` alone against a stored `term_start` would have written a window in which `in_term()` is false for every date. |
| **Known risks** | **Two migrations must be run by anyone restoring an older dump**: `migrate_reteach_targets.py` and `migrate_course_terms.py`. **`ALIGNMENT_REFUSAL_THRESHOLD` is stale** — still 0.70, measured against CSW2/CS-C only, and the corpus grew by 2,076 chunks; re-run `calibrate_threshold.py` before demoing DLD. **`ingest-003` is unfixed and is the sharpest one left**: retrieval has no completeness guard, so any interrupted ingest silently serves a partial book. **`admin-006`'s "refuse if cited" guard does not exist and cannot** — nothing persists a `chunk_id`. Auth tests still assert role guards by source inspection, never by a live 403 (raised by the owner, not yet tracked). |

### Session 014 — 2026-08-24 — teacher-008, admin-004, and three answers

| | |
|---|---|
| **Goal** | Four things raised while clicking through the harness: too few reteach units, "what is the verification queue", a 404 on admin Materials, and the audit log reading as machine output. |
| **Completed** | `teacher-008` (reteach drafts from both rankings — contract + schema change) and `admin-004` (audit log summaries, seed noise hidden — contract change). The 404 was not a backend bug: the harness sent `/admin/courses//materials` from an empty input box, which matched no route, so the API answered a perfectly correct "No such route." Guarded and prefilled. 295 tests (was 288). |
| **Verification run** | Both features verified live against the real corpus with re-runnable scripts; demo state reset afterwards. |
| **Evidence recorded** | `evidence/teacher-008/verification.txt`, `evidence/admin-004/audit-log.txt` |
| **Commits** | Two. |
| **What verifying found that reading would not have** | **Taken literally, "the top three of each ranking" produced TWO reteach units** against the real corpus — one misconception refused at 43% for lack of evidence, and two gaps were already covered by a misconception unit. Every one of those a correct decision, and the result is still an empty-looking panel, which is the opposite of what was asked for. A row that yields no unit now advances to the next candidate rather than consuming a slot; the run then filled 3/3 and 3/3. **Overlap coverage was only recorded on the create path**, so a second press skipped the covering misconception as `already_drafted`, forgot the overlap, and drafted the duplicate the first press had correctly declined. **An audit row outlives what it points at** — a pruned reteach unit fell through to printing `reteach:32` back, the exact technical noise the summary field exists to remove. |
| **Known risks** | `teacher-008` needed `backend/scripts/migrate_reteach_targets.py` because `create_all()` does not alter an existing table — **it has been run against the shared Neon database, but a teammate restoring from an older dump must run it again.** The reteach panel holds one unit after a reset; fill it with `suggest-top` before the demo, not during. Everything else unchanged: `demo-001`, `a11y-001`, `auth-002` and `infra-001/003/005` still need other people. |

### Session 013 — 2026-08-24 — perf-001 and student-009

| | |
|---|---|
| **Goal** | Answer a report that "everything loads super duper slow, a button responds after a minute, and the MCQ selection is not persistent." |
| **Completed** | `perf-001` (request latency) and `student-009` (answers survive a reload, a contract change). 281 tests (was 272). |
| **Verification run** | `perf-001`: query counts instrumented per request; `student-009`: its ten verification steps run live via a new re-runnable script, then the whole golden path re-run clean — heatmap 7 → 8 — and demo state reset afterwards. |
| **Evidence recorded** | `evidence/perf-001/{measurements,query-counts}.txt`, `evidence/student-009/{verification,golden-path,demo-reset,diagnostic-resume,practice-resume}.txt` |
| **Commits** | Two. |
| **What verifying found that reading would not have** | **The slowness was never the app code** — `/languages` (no DB) answers in 7ms while `/health` (one `SELECT 1`) took 1.6–5.6s. Measuring separated the two costs that matter: opening a Neon connection is ~3.5s, running a query on an open one is ~0.12s. Every fix follows from that 30× gap, and the pool was raised *and pre-warmed in parallel* only because 20 connects take 71s sequentially but 6s in parallel — raising the pool without warming it made a burst measurably **worse** (11.3s vs 6.4s) before warming was added. **Three stale uvicorns from the previous day** were still running on 8011/8012/8013 against the same database. **`reset_demo_state.py` knew nothing about the new `diagnostic_responses` table**, so a pre-demo reset would have left the diagnostic opening with every option already selected from the last rehearsal — the app appearing to answer its own questions, on stage. And a batching edit left `latest` undefined at two call sites, turning `submit_diagnostic` into a 500 that only a live request surfaced. |
| **Known risks** | **The latency floor is not fixed and cannot be fixed from this repo.** The compute is a shared 0.25 vCPU ~4,000 km away and queries largely serialise, so ~5 queries per request is a hard floor of roughly half a second; 20-client bursts still ranged 4.7–16.9s. `get_db()` also still holds a pooled connection across the whole provider call — releasing it around the LLM call touches every router and was judged too big for the time left. **Hit `/health` once after starting the backend** so the pool is warm before anyone clicks. `demo-001`, `a11y-001`, `auth-002` and `infra-001/003/005` remain blocked on other people, unchanged. |

### Session 012 — 2026-08-24 — infra-006, all teacher panels, all admin, i18n, a11y backend, demo prep

| | |
|---|---|
| **Goal** | Work the owner's order: infra, then the teacher and admin panels, then i18n, then a11y, then demo prep. |
| **Completed** | `infra-006` (seed pruning); `teacher-002/003/005/006/007` plus `GET /teacher/reteach` and `GET /student/assignments`; `admin-001/002/003` (a whole new `routers/admin.py`); `i18n-001`; the backend half of `a11y-001`; and `demo-001` prep including writing `docs/demo-script.md`, which did not exist. 271 tests (was 200). **Every backend feature is now passing.** |
| **Verification run** | Each feature verified live against the real database and the real provider chain, with evidence recorded per feature. The golden path was then re-run end to end from a clean state — diagnostic → gap attributed to CSW1 → lesson at 66% with real page citations → scoped practice → wrong answer → the specific misconception → confirm → **heatmap 7 → 8** → deny → unchanged — and again fully offline with `PROVIDER=mock`. |
| **Evidence recorded** | `evidence/infra-006/`, `evidence/teacher-00{2,3,5,6,7}/`, `evidence/admin-00{1,2,3}/`, `evidence/i18n-001/`, `evidence/a11y-001/`, `evidence/demo-001/` |
| **Commits** | Six. |
| **What verifying found that reading would not have** | Nine real bugs, every one caught by running the thing rather than by inspecting it. **i18n:** the request's `language` was used as the *source* of the inbound translation, so an English question sent with `language=hi` was translated as though it were Hindi — not a no-op; Sarvam rewords it, the reworded text is embedded, and it retrieves different passages. The same question scored 88% in English and 82% in Hindi with different citations. **i18n:** `language` defaulted to `"en"`, so a student's saved `preferred_language` did nothing. **teacher-005:** reported `delta_share -0.3462` seconds after a reteach was approved — zero confirmations became a share of zero and subtracted into a triumphant negative delta while nobody had been asked. **teacher-006:** the 422 branch read a variable bound only on the success path, so an honest refusal raised `UnboundLocalError` and became a 500; the branch fires on real misconceptions. **contract:** `GET /student/assignments` was in the frozen contract and never built, so an approved reteach unit went nowhere — the gate opened onto a wall. **contract:** audit actions were derived from the resulting status (`sourced_content.approved`) where the contract documents the verb (`.approve`), and those strings are what an admin types into `?action=`. **infra-006:** the first prune deleted ten PH101 practice items because it was not course-scoped — right outcome, wrong rule. **mock:** an unrehearsed offline question returned Newton's-laws text under a Django question at 80% alignment with five real Django citations. **mock:** its practice distractor named a misconception deleted with the physics course, so offline a wrong answer diagnosed as *nothing* — and the test covering it passed because it hardcoded the same dead slug. |
| **Known risks** | **`demo-001` is the only thing that matters now and one person cannot close it.** It needs two laptops and a second operator; `docs/demo-script.md` is written and is what to run. **Rehearse its exact questions while online** — offline fidelity comes from the disk cache, not from the mock. **`a11y-001` and `auth-002` are blocked on frontend pages that do not exist** (`frontend/src/pages/*` are all `.gitkeep`); the backend halves are done, and read-aloud must use the new `TutorResponse.speech_text`, never `body`. **`infra-001/003/005` still need one teammate each** to confirm from another machine. **The two ingest HTTP endpoints are deliberately NOT built** and marked so in the contract — they need an `ingest_jobs` table, and `ingest-001` already ships through `scripts/ingest_pdfs.py`. |
| **Next best action** | Get a second person and run `docs/demo-script.md` twice: once clean and online, once with the wifi off. That is the last thing standing between this build and the deadline. |

### Session 011 — 2026-08-24 — student-008 (syllabus upload) + student-007 (mastery)

| | |
|---|---|
| **Goal** | Build the one endpoint the frozen contract promised and nobody had written, then the mastery view. |
| **Completed** | `POST /student/syllabus-upload` (`services/syllabus.py`, `prompts/syllabus_coverage.md`, a mock-provider branch, `python-multipart`) and `GET /student/mastery`. 200 tests (was 172). The contract is updated for both, including the upload's failure modes. **The student surface is now complete — no student endpoint in the contract is unbuilt.** |
| **student-008 — the design that matters** | Coverage bias runs **opposite** to `guardrail.py`, deliberately. There, doubt resolves toward answering, because a wrong refusal blocks a student who came to learn. Here doubt resolves toward *creating the gap*: a false gap is a skippable lesson the student can see is wrong, while a false coverage is a real gap nobody ever finds. Visible over-detection beats invisible under-detection. Three guards enforce it — a text-free PDF is refused with `no_text_found` rather than read as "covers nothing", a concept missing from the model's reply counts as not covered, and a provider outage is a 503 and never an empty verdict. Each, done the other way, returns a confident-looking gap list built from zero evidence. No mastery is written: a syllabus is evidence of exposure, not of learning. |
| **Verification run** | Three syllabi chosen so a rubber stamp in *either* direction fails: a genuine CSW1 → 0 gaps; an ECE numerical-methods course → all 8; and the discriminating one, a Python-OOP-and-venv course with no web or database content → exactly the 6 it does not teach, identical as `.txt` and as a real PDF. One of those gaps then taught at 77% alignment with 5 citations. A real, valid, text-free PDF was refused. Mastery verified from a clean slate: all `untested`, then the diagnostic drove six `solid` and two `shaky`, then a correct practice answer moved one back to `solid`. |
| **Evidence recorded** | `evidence/student-008/syllabus-upload-live.txt`, `evidence/student-007/mastery-live.txt` |
| **Commits** | Two. |
| **Two bugs found by verifying rather than by reading** | `_plain_text()` gated on the file extension, so a plain-text syllabus named `.pdf` was rejected — contradicting `extract_text()`'s own docstring that byte-sniffing makes the extension irrelevant. Type is now decided by the printable-character ratio after decoding, since latin-1 decodes any byte sequence and "it decoded" was never evidence the upload was text. Separately, the mastery view exposed a **phantom concept**: `model-fields`, dropped from `concepts.json` at 0.56, was still a row in the shared DB because `seed.py` upserts and never deletes. It was invisible until an endpoint enumerated the whole syllabus. Orphan deleted (zero dependents); the code fix is `infra-006`. |
| **Known risks** | **`infra-006` is unfixed** — the next concept anyone removes from a seed file will linger the same way, and only a whole-course listing will show it. A prune must refuse to delete a concept with dependents, or it takes a student's history with it. **The syllabus check costs one LLM call per upload** and is cached on the file's text, so a re-upload of the same syllabus is instant but a fresh one is not. **`infra-001`, `infra-003`, `infra-005` are still waiting on a second person** — assumed working for now at the owner's direction, but nobody has confirmed the tunnel from another machine. |
| **Next best action** | `demo-001`, the two-laptop rehearsal — the demo content is real, the student surface is complete, and it is the only thing left that finds problems no test can. Then the seeded teacher/admin panels, which are read endpoints over data already in the DB. |

### Session 010 — 2026-08-24 — content-001: CSW2 replaces physics as the demo course

| | |
|---|---|
| **Goal** | Finish the half-done seed migration found uncommitted in the working tree: make CSW2 the demo course so the demo runs on a real ingested book instead of an 18-chunk physics stand-in. |
| **Completed** | Found the migration mid-flight and internally inconsistent — `concepts.json` had dropped two concepts that `diagnostic.json`, `practice.json` and `demo_class.gap_counts` still referenced, so `seed.py` failed validation with 6 errors and the seed could not run at all. Resolved it, verified the whole thing live, and recorded evidence. Also corrected `infra-005` from `in_progress` to `blocked` — it is waiting on a second person, and a stale `in_progress` is what the next session picks up first. |
| **The actual problem** | The two concepts were dropped for a good reason: `python-classes-objects` (0.4591) and `html-forms` (0.4892) fail the *entailment* half of the evidence check against the Django book, which uses classes and forms on every page and teaches neither. Their gap lessons correctly refuse — right behaviour, wrong place, because golden path step 2 opens exactly that lesson. But deleting them was the worse option: `seed.py`'s `add_diagnoses()` silently `continue`s past a misconception whose `problem_type` has no practice item, so removing their two practice items would have emptied two heatmap rows (4 and 3 confirmed) **without raising anything**. So they were **demoted** — `prerequisite_course` removed — which makes them untestable by the diagnostic while keeping the practice items and heatmap rows alive. The two freed diagnostic slots went to `virtual-environments` and `url-routing`, whose misconceptions already existed and were unused. The diagnostic now tests exactly the 8 prerequisite concepts, 1:1. |
| **Verification run** | `seed.py` validates with 0 errors and seeds clean (30 confirmed diagnoses, both at-risk heatmap rows intact). All 15 concepts run through the FULL evidence check against the real CSW2 corpus: **all 8 prerequisites sufficient**, so no diagnostic wrong answer can reach a refusing lesson. Then `reset_demo_state.py` for a clean slate and the golden path end to end in one run through the live provider: 8-item diagnostic → 2 gaps attributed to CSW1 → both lessons answer (venv citing pp. 47–48; url-routing at 62% citing pp. 114/116/124, the lesson itself stating patterns are matched in order — the exact misconception the wrong answer encoded) → 3 generated venv-scoped practice items → wrong answer → "Believes a globally installed package is available inside a virtual environment" → confirm → heatmap gains that row → deny → unchanged. 172 tests, `./init.sh` green. |
| **Evidence recorded** | `evidence/content-001/concept-evidence-check.txt`, `evidence/content-001/golden-path-csw2.txt` |
| **Commits** | One. |
| **Known risks** | **`url-routing` is the thin one: top similarity 0.7274 against a 0.70 gate.** It is now both a diagnostic item and a `gap_counts` entry, and `calibrate_threshold.py` suggests 0.72 for this corpus — which would leave it 0.0074 of headroom. Do not raise the threshold without re-measuring that concept. **The demo's live increment currently creates a new heatmap row at 1 rather than growing a bar**, because the two new diagnostic items map to misconceptions with no seeded history; for the stage, have the student miss the HTTP-methods item instead, whose misconception is seeded at 7 and will visibly go 7 → 8. **PH101/PH000 are still in the database** — harmless, since everything is course-scoped, but a teammate poking at the DB will see two dead courses. **CSW1 has no corpus** and needs none: it is only ever named as the course a gap should have come from. |
| **Next best action** | `student-007` (mastery view), then the seeded teacher/admin panels. `demo-001` (two-laptop rehearsal) is now the highest-value non-feature work and is fully unblocked — the demo content is real. |

### Session 009 — 2026-08-24 — golden path COMPLETE + student-004, teacher-004

| | |
|---|---|
| **Goal** | Finish the golden path (`student-005` → `student-006` → `teacher-001`), then the two nearly-free wins. |
| **Completed** | `services/practice.py`, `routers/teacher.py`, practice/confirm routes on the student router, `prompts/{practice_generate,practice_explain}.md`. Mock provider extended so `PROVIDER=mock` still yields a *diagnosable* item and guardrail hints. 170 tests (was 149). |
| **Verification run** | One live run of the whole golden path: 4 deliberate wrong diagnostic answers → 4 named gaps → lesson at 84% with 5 citations → 3 generated practice items scoped to that gap (a second gap gave entirely different items, 0 shared prompts) → answered 15 N on a 30 N @ 30° item → the specific sin/cos-swap diagnosis → confirm → heatmap 7→8 → deny → unchanged. Teacher payloads carry no id, name or email; students get 403. |
| **Evidence recorded** | `evidence/student-004/show-source-live.txt`, `evidence/student-005/practice-live.txt`, `evidence/student-006/misconception-live.txt`, `evidence/teacher-001/heatmap-live.txt`, `evidence/teacher-004/uncertainty-flags-live.txt` |
| **Commits** | One. |
| **Known risks** | **The demo database has accumulated verification artefacts** — repeated runs left five duplicate "French Revolution" uncertainty flags and extra practice sets/attempts. It is all real data, but the flags panel looks repetitive; `reset_db.py` + `seed.py` before the demo cleans it, at the cost of re-seeding. **PH101 is still the 18-chunk stand-in corpus**, so a `student-004` citation there names a page with no PDF behind it — CS-C and CSW2 resolve exactly. Practice generation costs one LLM call and took a few seconds per set; `POST .../answer` costs another for the explanation. Both are cached, so a rehearsed demo is fast, but a judge asking for a brand-new gap's practice will wait. |
| **Next best action** | `student-007` (mastery view) — the rows are already written by the diagnostic and by every practice answer, so it is one read endpoint. Then the seeded teacher/admin panels. `demo-001` (two-laptop rehearsal) is now unblocked and is the highest-value non-feature work left. |

### Session 008 — 2026-08-24 — infra-005, student-001/002/003, rag-004

| | |
|---|---|
| **Goal** | Tunnel for the team, then the golden path chain, then the graded-work guardrail against real assignment PDFs. |
| **Completed** | `tunnel.sh`; `routers/student.py` (course summary, diagnostic, submit, gaps, gap lesson); `tutor.lesson()`; `services/guardrail.py`; `prompts/{gap_lesson,guardrail_intent,guardrail_hints}.md`. Ingestion now skips material already present, so an assignment uploaded mid-semester does not re-embed the textbook. 149 tests (was 96). |
| **Verification run** | Ingested a second real course, CSW2: *Django 5 By Example* (1190 pages → 1938 chunks) plus the seven ITER assignment PDFs, all page-verified. Golden path steps 1–2 run live as the seeded physics student: four deliberate wrong answers → four named gaps → a lesson at 84% closing on the sin/cos swap the wrong answer encoded. Guardrail run live on a question copied verbatim out of Assignment 1. Tunnel verified through the public URL: CORS, login, 401, and `/tutor/ask`. |
| **Evidence recorded** | `evidence/infra-005/tunnel-verification.txt`, `evidence/student-00{1,2,3}/*.txt`, `evidence/rag-004/guardrail-live.txt` |
| **Commits** | Three: `infra-005`, the student chain, `rag-004`. |
| **Known risks** | **`POST /student/syllabus-upload` is in the contract but not built** — the alternative diagnostic entry for incoming students. It is in no verification step, but a frontend teammate reading the contract will expect it. **CSW2 has no concepts, diagnostic or misconceptions**, so the gap→lesson→practice chain cannot run on it; the guardrail demo there calls `tutor.lesson()` with a concept name directly. The demo course remains `PH101`. The physics corpus is still the 18-chunk stand-in, not a real PDF — `student-004` Show Source will name a book and page that no file on disk can be opened at, unlike CS-C and CSW2. |
| **Next best action** | `student-004` and `teacher-004` — both are one read endpoint over data that already exists, and both are explicitly flagged as high judging value for very little work. Then `student-005` → `student-006` → `teacher-001` closes the golden path. |

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
