# Team Roles and How It Merges

SOAIDEATHON-S28 · 6 people · 36 hours

This reconciles the original roles guide with how the repo is actually set up. Where they differ, this file wins.

## The one rule

Agree the shape of the data before anyone builds. That shape is `docs/api-contract.md`. Frontend builds against a fake version of a response, backend builds the real one, and they meet without conflict because neither ever changed the shape.

The contract is **frozen at hour 4**. After that, you change the contract file first, announce it, then change code.

## The six roles

### 1. Frontend - Student Dashboard

Owns: login, course summary, gap check, lesson cards, practice, quiz, misconception confirm, mastery tracker.

Files: `frontend/src/pages/student/`

Done means: every screen calls the shape in the contract and renders all of its states, including the two refusal states. Real data can come later.

Blocks nobody. Needs the contract only.

### 2. Frontend - Teacher Dashboard

Owns: misconception heatmap, reasoning paths, gap map, uncertainty flags, before/after, reteach approval, verification queue.

Files: `frontend/src/pages/teacher/`

Done means: same, plus every list has an empty state. Most teacher views start empty and fill during the demo.

Blocks nobody.

### 3. Frontend - Management Dashboard

Owns: curriculum upload, course and prerequisite structure, audit log, and the auth screens (login, signup, forgot password).

Files: `frontend/src/pages/admin/`, `frontend/src/pages/auth/`

Done means: same. Forgot password is UI only and must not make a network call.

Blocks nobody.

### 4. Backend - API and data

Owns: auth, database models, ingestion and chunking, course and prerequisite structure, quiz engine, gap detection, seeding, and every HTTP endpoint.

Files: `backend/app/models.py`, `backend/app/db.py`, `backend/app/routers/`, `backend/scripts/`

Done means: the endpoint matches the contract and returns real data from the database.

Frontend does not wait on you. They build against fakes with the same shape.

### 5. AI/ML - the tutor engine

Owns: retrieval, the alignment score, the refusal rule, the graded-work guardrail, the misconception matcher, prompts, and the provider layer with its cache and fallbacks.

Files: `backend/app/services/`, `backend/app/providers/`, `prompts/`

Done means: a plain Python function returns a structured object with a confidence score attached, not a paragraph of prose.

The interface with backend is a **function signature, not HTTP**. Agree it in one message, then work independently. Backend wraps your function in a route and can build that route around a canned response while you are still working.

### 6. Integration and demo lead

Owns: wiring real endpoints to real frontend calls, seed data for everything not fully live, `docs/demo-script.md`, rehearsal, and the deck.

Done means: the golden path runs start to finish with nobody standing behind a laptop explaining what would happen.

Check in with every pair throughout. Do not parachute in at hour 30.

## Two jobs nobody owned

These are in the problem statement, so they are scored. Assign them or they will not happen.

- **Multilingual and accessibility** (`i18n-001`, `a11y-001`). Read-aloud, font size, contrast, language switch. Roughly one hour of work for a whole judging criterion.
- **The deck and the pitch.** SIH weighs presentation heavily. Suggested owner: the integration lead.

## Merge order

1. **Skeleton and contracts.** Repo structure, design tokens, database models, API contract - merged to main together, before anyone splits off. *(Done: `cc24ce1`, `c2f7760`.)*
2. **Parallel build.** Everyone on their own branch, in their own folder, merging small and often. Not one giant merge at the end.
3. **Real-logic swap.** Backend and AI/ML replace canned responses with real ones. The shape never changed, so frontend touches nothing.
4. **Integration and demo.** Golden path fully live, everything else seeded, rehearsed twice.

## Branch and commit rules

- Branch per feature: `feat/<feature-id>-<slug>`, e.g. `feat/student-003-gap-lesson`.
- Commit small and often. Push at least every hour so nobody's work is trapped on one laptop.
- `main` must always be green: `./init.sh` passes before you merge.
- If you touch a file you do not own, say so in the team channel first.
- Never commit `.env`, `node_modules/`, or `.venv/`.

## What "done" means here

The roles guide says done is "renders whatever comes back". That is right for stage 2 only. For a feature to be marked `passing` in `feature_list.json`, all of this must be true:

1. The `verification` steps for that feature were run exactly as written.
2. The actual output is saved under `evidence/<feature-id>/`. The real terminal text or a screenshot, not a description of it.
3. `./init.sh` still passes.
4. It is committed.

If you cannot produce the evidence, it is not passing. Only one feature may be `in_progress` at a time.

## The trap that will cost you the demo

Every tutor response has an `outcome` field with three possible values:

- `answered` - normal explanation with citations and an alignment score
- `insufficient_evidence` - the tutor refused because the curriculum does not cover it
- `graded_work_refused` - the tutor refused because it is graded work, and returned hints

All three arrive as HTTP 200, because a refusal is a **correct** response, not an error. If a screen only handles `answered`, the two features the judges care most about render as blank cards. Handle all three or the build looks broken exactly when it is working.
