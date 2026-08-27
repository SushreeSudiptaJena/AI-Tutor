# Deploying on Render

One web service. FastAPI serves the API **and** the built frontend from the
same origin, so there is no CORS hop, no second service to wake, and one URL to
put on a slide.

The database is **not** part of the deploy. The app runs against the existing
Neon instance in `ap-southeast-1`, which already holds the ingested chunks and
their embeddings. Render must not create one.

---

## What is in the repo

| File | Does what |
|---|---|
| `render.yaml` | The blueprint. One `type: web`, `runtime: python`, `plan: free`, `region: singapore`. |
| `render-build.sh` | Installs Python deps, builds the frontend, pre-fetches the embedding model. |
| `.python-version` | `3.14.3` — the version the test suite was verified on. |
| `frontend/.env.production` | Sets `VITE_API_BASE=` (empty) so the bundle calls relative paths. |

---

## Deploying

1. Push `main`. (Already done if you are reading this after the deploy commit.)
2. Render dashboard → **New** → **Blueprint** → pick the `AI-Tutor` repo.
   Render reads `render.yaml` and shows one service, `ai-tutor`.
3. It prompts for the five secrets, because they are `sync: false` in the
   blueprint and were never committed. Paste each from your local `.env`:

   ```
   DATABASE_URL
   FALLBACK_API_KEY_GROQ
   FALLBACK_API_KEY_GEMINI
   GLM_API_KEY
   SARVAM_API_KEY
   ```

   Keep `?sslmode=require` on the end of `DATABASE_URL`.
4. **Apply**. First build takes roughly 5–8 minutes: onnxruntime and PyMuPDF
   are large wheels, and the frontend build and model download follow.
5. When it goes live, open the service URL. `/health` should answer
   `{"status":"ok","db":"ok"}`. If `db` says anything else, `DATABASE_URL` is
   wrong or Neon is asleep — hit it again.

Nothing needs seeding: the Neon instance is already populated. If you ever do
need to reset it, run `backend/scripts/reset_db.py` and `seed.py` **locally**
against the same `DATABASE_URL`, not on Render.

---

## Known limits of the free tier

These are real and will show up during a demo. Read them before presenting.

**It sleeps after 15 minutes idle.** The first request after that takes ~50s
while Render starts the container. Everything is fine once it is awake.
*Mitigation: open the URL five minutes before you present and leave the tab
open.*

**Memory is 512MB.** FastAPI plus onnxruntime with the BGE model loaded is the
tightest thing in the deploy. If the service restarts with an out-of-memory
message in the logs after the first question, that is this. The fix is the
$7/mo Starter plan (2GB) — change `plan: free` to `plan: starter` in
`render.yaml` and redeploy.

**Uploaded files do not survive a restart.** `admin.py`, `admin_batches.py`
and `teacher.py` write uploads to `backend/data/pdfs/`, which is ephemeral on a
free instance. Ingestion writes its *chunks and embeddings to Neon*, so
retrieval and citations keep working — only the original PDF is gone. Uploading
during the demo is fine; uploading and expecting the file next week is not.

**The LLM disk cache starts empty and resets on each deploy.** `backend/.cache`
is gitignored, so the deployed service does not inherit your warm local cache.
The first run of each prompt pays full provider latency. *Mitigation: click
through the golden path once after deploying, which warms the cache for the
demo.* A persistent disk (paid plans only) would keep it.

**The embedding model is pre-fetched at build time**, not at runtime — that is
what `FASTEMBED_CACHE_PATH` and the last step of `render-build.sh` are for.
Without it, the first student to ask a question after every wake-up would wait
for a ~130MB download on top of the ~50s cold start.

---

## How the single service routes

`backend/app/main.py` mounts `/assets` and registers a catch-all **after** all
routers, so every real endpoint matches first.

The catch-all splits on the `Accept` header, not on a path prefix. This is
deliberate and worth not "simplifying":

- The frontend and the API genuinely share paths. `/admin` and `/teacher` are
  both React Router routes *and* API router prefixes. Any prefix rule breaks
  one side — a prefix list returns JSON 404 when you hard-refresh `/teacher`,
  and no list at all returns the HTML shell to a `fetch()` that then dies on
  `Unexpected token '<'`.
- A browser navigating sends `Accept: text/html`. Every call from
  `frontend/src/lib/api.ts` is a `fetch()` with `Accept: */*`.

So an unknown path answers the SPA shell to a navigation and the contract's
JSON error envelope to a fetch. Verified for both, including the overlapping
`/admin`, `/admin/login` and `/teacher` paths — see
`evidence/deploy-render/verification.txt`.

The root `/` is special-cased ahead of that check and always returns the shell.
Nothing in the API owns it, and leaving it to the `Accept` rule meant a bare
`curl <url>/` got a JSON 404 — which reads as a broken static mount when it
isn't.

---

## Local development is unchanged

`frontend/dist` may not exist locally, and `main.py` skips the whole static
block when it doesn't. `npm run dev` still serves the frontend on :5173 against
`frontend/.env.local`, which takes precedence over `.env.production`. The
cloudflared tunnel in `init.sh` still works for anyone who wants it.
