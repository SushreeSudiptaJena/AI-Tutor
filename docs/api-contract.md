# API Contract

**Status:** draft · **Freeze at hour 4.** After the freeze, this file changes *before* the code does — edit here, announce in the team channel, then implement.

This is the interface between one backend and five frontend people. It covers **every** feature in `feature_list.json`, not just the golden path, so nobody is blocked waiting for a decision.

---

## Conventions

| | |
|---|---|
| **Base URL** | `VITE_API_BASE` (the tunnel URL). No `/api` prefix. |
| **Content type** | `application/json` everywhere except file upload (`multipart/form-data`) and SSE. |
| **Case** | `snake_case` in all request and response bodies. |
| **Auth** | `Authorization: Bearer <token>` on everything except `/health`, `/languages`, `/auth/signup`, `/auth/login`. |
| **Timestamps** | ISO 8601, UTC, `Z` suffix. e.g. `2026-08-23T11:48:25Z` |
| **IDs** | Integers, except the session token (opaque string). |
| **Pagination** | `?limit=` (default 50, max 200) and `?offset=`. Responses wrap in `{ "items": [...], "total": n }`. |

### Error envelope

Every non-2xx response, without exception:

```json
{ "error": { "code": "insufficient_evidence", "message": "Human-readable.", "detail": {} } }
```

| Code | Meaning |
|---|---|
| 400 `bad_request` | Malformed input |
| 401 `unauthenticated` | Missing / invalid / logged-out token |
| 403 `forbidden` | Valid token, wrong role |
| 404 `not_found` | |
| 409 `conflict` | e.g. email already registered |
| 422 `validation_error` | `detail` carries per-field messages |
| 503 `provider_unavailable` | All LLM providers failed, including fallbacks |

### Roles

`student` · `teacher` · `admin`. A 403 is returned when the role does not match the route prefix. `/tutor/*` is student-only.

---

## Shared objects

Referenced throughout. Defined once here.

### `User`
```json
{
  "id": 1,
  "email": "asha@example.edu",
  "full_name": "Asha R",
  "role": "student",
  "course_id": 3,
  "preferred_language": "en"
}
```

### `Citation` — `rag-001`, `student-004`
Produced by retrieval (`rag-001`) and attached to anything the tutor generates. **Never empty on an answered response** — that is the whole point of the build.
```json
{
  "chunk_id": 812,
  "material_id": 4,
  "book_title": "Concepts of Physics, Vol 1",
  "page_no": 143,
  "chapter": "5. Newton's Laws of Motion",
  "snippet": "…the net force on a body equals…"
}
```

### `EvidenceReport`
The alignment score (`rag-002`) and the refusal decision (`rag-003`) come from one object.
```json
{
  "alignment_score": 0.82,
  "alignment_percent": 82,
  "top_similarity": 0.79,
  "threshold": 0.68,
  "sufficient": true,
  "reason": null
}
```
`alignment_percent` is what the UI renders. When `sufficient` is `false`, `reason` is a short string and the caller receives a refusal outcome instead of prose.

`reason` values: `no_matching_material` (top similarity below `threshold`, or nothing retrieved for the course) · `material_does_not_answer` (the material is close but an entailment check says it does not contain what the question needs). The teacher dashboard groups uncertainty flags by this field.

`threshold` is a property of the **ingested corpus**, not a constant — it is re-measured with `backend/scripts/calibrate_threshold.py` after each ingest and read from `ALIGNMENT_REFUSAL_THRESHOLD`. Frontend must render whatever the API returns rather than hard-coding a number.

### `Gap`
```json
{
  "id": 21,
  "concept": "Vector components",
  "prerequisite_course": "Class 12 Physics",
  "detected_from": "diagnostic",
  "status": "open",
  "suggested_prompts": [
    "Explain vector components to me",
    "Why do we resolve forces into components?"
  ],
  "latest_practice_set_id": 84
}
```
`detected_from`: `diagnostic` | `syllabus_upload` | `practice`. `status`: `open` | `improving` | `closed`.

`latest_practice_set_id` is the most recent practice set generated for this gap,
or `null` if there is none. It exists so a client can **resume** a half-finished
practice set after a reload without having stored the id itself — hand it to
`GET /student/practice/{practice_set_id}`. It is not a prompt to auto-generate:
`null` means "offer the practise button", not "call generate".

Gaps are **persisted rows, not a one-off result**. `POST /student/diagnostic/{id}/submit` writes them and returns them in the same transaction so the UI can render immediately, but they remain available from `GET /student/gaps` afterwards — for the dashboard, the mastery view, or as chat prompt suggestions. `suggested_prompts` exists so the chat can offer a starting question without the frontend inventing phrasing.

### `TutorResponse` — discriminated on `outcome`
Every tutor-generated response uses this shape. **Frontend must branch on `outcome`.**

```json
{
  "outcome": "answered",
  "language": "en",
  "body": "A vector's components are…",
  "citations": [ /* Citation */ ],
  "evidence": { /* EvidenceReport */ }
}
```
```json
{
  "outcome": "insufficient_evidence",
  "language": "en",
  "body": "I don't have approved course material covering this. I've flagged it for your teacher.",
  "citations": [],
  "evidence": { "sufficient": false, "alignment_percent": 11, "reason": "no_matching_material" },
  "uncertainty_flag_id": 55
}
```
> **Where the guardrail runs.** `graded_work_refused` can only be returned by
> **`POST /tutor/ask`**. It is never returned by `/student/gaps/{id}/lesson`,
> `/student/practice/*`, or any other route — those are driven by a concept or a
> generated item, not by text the student typed, so a refusal there would only
> ever be a false positive.
>
> Two conditions must **both** hold to refuse: the message matches assignment
> material (similarity > 0.80), **and** an intent check classifies it as asking
> for the solution rather than for understanding. "Solve Q3" is refused;
> "why does Q3 use conservation of momentum?" is answered in full, with citations.

```json
{
  "outcome": "graded_work_refused",
  "language": "en",
  "body": "This looks like it's from a graded assignment, so I won't solve it. Here's how to approach it.",
  "hints": ["Start by resolving the force into components.", "…"],
  "citations": [ /* Citation */ ],
  "matched_assignment": { "material_id": 9, "title": "Problem Set 3" }
}
```

### `Misconception`
```json
{
  "id": 7,
  "label": "Treats velocity as implying a net force",
  "topic_id": 12,
  "problem_type": "newtons-second-law",
  "confirmed_count": 14
}
```

### `PracticeItem`
```json
{
  "id": 301,
  "prompt": "A 2 kg block slides at constant velocity…",
  "kind": "mcq",
  "options": ["…", "…", "…", "…"],
  "gap_id": 21,
  "citations": [ /* Citation */ ]
}
```
`kind`: `mcq` | `numeric` | `short_text`. `options` present only for `mcq`. **Correct answers are never sent to the client.**

---

## System

| Method | Path | Feature | Returns |
|---|---|---|---|
| `GET` | `/health` | infra-002 | `{ "status": "ok", "db": "ok" }` — see note |
| `GET` | `/meta/provider-status` | infra-004 | active provider, fallback chain, cache warmth — see below |
| `GET` | `/languages` | i18n-001 | `{ "items": [ { "code": "en", "label": "English" }, { "code": "hi", "label": "हिन्दी" } ] }` |

`/meta/provider-status` exists so the demo can prove on screen which provider is live and that the cache is on.

`/meta/provider-status` returns:

```json
{ "active": "groq",
  "fallbacks_available": ["gemini", "groq"],
  "cache_enabled": true,
  "chain": ["groq:openai/gpt-oss-120b", "gemini:gemini-3.6-flash",
            "glm:glm-4.5-flash", "groq:qwen/qwen3.6-27b", "mock:mock-1"],
  "cache": { "entries": 42, "bytes": 18320, "enabled": true } }
```

`chain` is ordered by **measured** latency and always ends in `mock:`, so a
machine with no keys and no network still answers. `cache.entries` shows how
warm the cache is — useful to display during the demo as proof the answers are
being replayed rather than re-generated.

**`/health` is always 200 while the process is up.** If the database is unreachable it returns
`{ "status": "degraded", "db": "<ErrorType>" }` rather than a 5xx, so a dropped free-tier
connection reads as "database down", not "app dead". Treat `status != "ok"` as a warning banner,
never as a fatal error.

---

## Auth — `auth-001`, `auth-002`

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/auth/signup` | `{ email, password, full_name, role, course_id? }` | `201 { token, user }` |
| `POST` | `/auth/login` | `{ email, password }` | `200 { token, user }` |
| `POST` | `/auth/logout` | — | `204` |
| `GET` | `/auth/me` | — | `200 User` |
| `PATCH` | `/auth/me/preferences` | `{ preferred_language }` | `200 User` |

- `token` is an opaque UUID stored in a `sessions` table. **Not a JWT** — do not attempt to decode it client-side.
- Wrong password → `401 unauthenticated`. Existing email on signup → `409 conflict`.
- Logout invalidates the token server-side; the next call returns `401`.

> **Forgot password has no endpoint.** `auth-002` is UI-only by decision: the screen collects an email and shows confirmation copy. **The frontend must not issue a network request.** Do not add `POST /auth/forgot-password` — its absence is intentional.

---

## Admin — `admin-001`, `admin-002`, `admin-003`, `ingest-001`

Structure (`admin-002`):

| Method | Path | Notes |
|---|---|---|
| `GET` | `/admin/departments` | `{ items: [{ id, name }] }` |
| `POST` | `/admin/departments` | `{ name }` |
| `GET` | `/admin/courses` | `{ items: [Course] }` |
| `POST` | `/admin/courses` | `{ code, title, department_id, prerequisite_course_ids: [] }` |
| `GET` | `/admin/courses/{course_id}` | single `Course` |

```json
// Course
{ "id": 3, "code": "PH101", "title": "Mechanics", "department_id": 1,
  "prerequisite_courses": [ { "id": 1, "code": "PH000", "title": "Class 12 Physics" } ] }
```

Curriculum upload and versioning (`admin-001`):

| Method | Path | Notes |
|---|---|---|
| `POST` | `/admin/courses/{course_id}/materials` | `multipart`: `file`, `kind`, `title`, `chapter_map?` |
| `GET` | `/admin/courses/{course_id}/materials` | `?include_archived=false` |
| `GET` | `/admin/materials/{material_id}` | single `Material` |
| `POST` | `/admin/materials/{material_id}/archive` | `200 Material` with `status: "archived"` |
| `GET` | `/admin/materials/{material_id}/versions` | `{ items: [Material] }`, newest first |

```json
// Material
{ "id": 4, "course_id": 3, "title": "Concepts of Physics, Vol 1", "kind": "textbook",
  "version": 2, "status": "active", "page_count": 412,
  "uploaded_by": "admin@example.edu", "uploaded_at": "2026-08-23T09:00:00Z",
  "ingest_status": "complete", "chunk_count": 1840 }
```
`kind`: `syllabus` | `textbook` | `notes` | `assignment`. `status`: `active` | `archived`.

> `kind: "assignment"` is what powers the graded-work guardrail (`rag-004`). Material uploaded as `assignment` is retrievable for *matching* but never quoted as an answer.

> Upload by a verified admin **counts as approval** for this build. There is no separate approval step for admin-uploaded material.

Ingestion (`ingest-001`):

| Method | Path | Notes |
|---|---|---|
| `POST` | `/admin/materials/{material_id}/ingest` | `202 { job_id }` — parse + chunk + embed |

> **NOT BUILT.** These two need an `ingest_jobs` table that does not exist, and `ingest-001` is already delivered through `backend/scripts/ingest_pdfs.py`. `POST /admin/courses/{id}/materials` stores the file and marks it `ingest_status: "pending"`; the script does the parsing and embedding. Do not build a frontend against the two rows below.

| `GET` | `/admin/ingest-jobs/{job_id}` | `{ job_id, status, pages_done, pages_total, chunk_count, error? }` |

`status`: `queued` | `running` | `complete` | `failed`. Frontend polls this; there are no websockets anywhere in this build.

Audit log (`admin-003`):

| Method | Path | Notes |
|---|---|---|
| `GET` | `/admin/audit-log` | `?limit=&offset=&actor=&action=` |

```json
{ "id": 88, "actor_email": "admin@example.edu", "action": "material.upload",
  "target": "material:4", "at": "2026-08-23T09:00:00Z", "detail": { "version": 2 } }
```
Actions: `material.upload` · `material.archive` · `material.ingest` · `course.create` · `reteach.approve` · `sourced_content.approve` · `sourced_content.reject`.

---

## Student

### Course scope — `student-001`
`GET /student/course-summary`
```json
{
  "course": { "id": 3, "code": "PH101", "title": "Mechanics" },
  "books": [ { "material_id": 4, "title": "Concepts of Physics, Vol 1",
               "pages": "1–212", "chapters": ["1. Introduction", "…"] } ],
  "topics": [ { "id": 12, "name": "Newton's Laws" } ]
}
```

### Prerequisite gap check — `student-002`

| Method | Path | Notes |
|---|---|---|
| `GET` | `/student/diagnostic` | `{ diagnostic_id, submitted_at, items: [PracticeItem] }` — each item carries `your_answer`. **`student-009`.** |
| `POST` | `/student/diagnostic/{diagnostic_id}/submit` | `{ answers: [{ item_id, answer }] }` |
| `POST` | `/student/syllabus-upload` | `multipart`: `file` — alternative entry for incoming students. **Built `student-008`.** PDF, `.txt` or `.md`; ≤10 MB. Returns the same `{ gaps, message }` body as `submit`. |
| `GET` | `/student/gaps` | `{ items: [Gap] }` |

Both submit paths return:
```json
{ "gaps": [ /* Gap */ ], "message": "Found 3 prerequisite gaps." }
```

A `Gap` from the upload carries `"detected_from": "syllabus_upload"` instead of
`"diagnostic"`. Nothing else differs — the same rows, the same
`GET /student/gaps`, the same `GET /student/gaps/{id}/lesson`. The field is for
the teacher's benefit, not for the frontend to branch on.

`POST /student/syllabus-upload` failure modes, all `400 bad_request` with the
reason in `error.detail.reason`:

| `reason` | When |
|---|---|
| `no_text_found` | The file has no text layer — a scan or a photo of a syllabus. **Not** treated as "covers nothing"; the student is asked for a text-based file. |
| `unsupported_type` | The bytes are not text and not a PDF (e.g. `.docx`). Judged by content, never by file extension. |
| `empty_file` | Zero bytes. |
| `file_too_large` | Over 10 MB. |
| `unreadable_pdf` | The PDF exists but will not open. |

A provider outage returns `503 provider_unavailable`. It never falls back to an
empty verdict, because "no gaps found" and "we could not check" must not look
alike to a student.

> **There is no score, percentage, or grade in this response, by design.** The problem statement asks for a gap list, not a grade. Frontend must not compute one from `answers`.

#### Resuming a diagnostic — `student-009`

`GET /student/diagnostic` replays what this student already picked, so a reload,
a dropped connection or coming back tomorrow does not mean answering eight
questions again:

```json
{
  "diagnostic_id": 3,
  "submitted_at": "2026-08-24T18:40:11Z",
  "items": [
    { "id": 121, "prompt": "…", "kind": "mcq", "options": ["…"],
      "concept": "HTTP methods, GET and POST",
      "your_answer": "GET, because it is a simpler request" },
    { "id": 122, "prompt": "…", "kind": "mcq", "options": ["…"],
      "concept": "URL routing", "your_answer": null }
  ]
}
```

* `your_answer` is the **exact string** the student sent, echoed back verbatim,
  or `null` for an item they never answered. Matching it against `options` to
  pre-select a button is the intended use.
* `submitted_at` is when the diagnostic was last submitted, or `null` if it
  never has been. Use it to decide between "start" and "resume", not to decide
  whether to render — a student may have answered some items and stopped.
* Re-submitting overwrites: one stored response per student per item, always
  the latest. There is no attempt history here.

> **`your_answer` does not weaken the no-score rule, and must not be used to
> get around it.** Only the answer *text* is stored — correctness is not, for
> diagnostic items, anywhere in the database. `correct_answer` still never
> leaves the server, so a client holding every `your_answer` still cannot mark
> a single one right or wrong, let alone total them. Do not add a `correct`
> field here.

### Lesson for a gap — `student-003`, `student-004`, `rag-002`
`GET /student/gaps/{gap_id}/lesson?language=en`

Returns a `TutorResponse`. `outcome` is normally `answered`; `evidence.alignment_percent` is the badge on the card, and `citations[]` powers **Show Source** — each entry resolves to a real `book_title` + `page_no`.

### Mastery — `student-007`
`GET /student/mastery`
```json
{ "items": [ { "topic_id": 12, "topic": "Newton's Laws",
               "concepts": [ { "id": 44, "name": "Free-body diagrams", "state": "shaky" } ] } ] }
```
`state`: `solid` | `shaky` | `untested`. **Built `student-007`.**

Written by two things, both already live: `POST /student/diagnostic/{id}/submit`
and `POST /student/practice/{id}/answer`. A correct practice answer moves a
concept back from `shaky` to `solid`, so the view shows recovery and not only
failure. `untested` is a real state, not a missing row — a concept nobody has
been asked about is genuinely unknown.

> No aggregate score and no time-on-task field exists anywhere in this response. That omission is the anti-surveillance stance — do not add one.

### Practice — `student-005`

| Method | Path | Notes |
|---|---|---|
| `POST` | `/student/practice/generate` | `{ gap_id, count? }` → `{ practice_set_id, items: [PracticeItem] }` |
| `GET` | `/student/practice/{practice_set_id}` | Re-read a set with the answers already given. **`student-009`.** |
| `POST` | `/student/practice/{practice_set_id}/answer` | `{ item_id, answer }` |

#### Resuming a practice set — `student-009`

`GET /student/practice/{practice_set_id}` returns the same `practice_set_id`,
`concept`, `source` and `items` that `generate` returned, with each item
carrying what the student did:

```json
{
  "practice_set_id": 84,
  "concept": "HTTP methods, GET and POST",
  "source": "generated",
  "items": [
    { "id": 310, "prompt": "…", "kind": "mcq", "options": ["…"], "gap_id": 486,
      "your_answer": "GET, because it is a simpler request",
      "correct": false,
      "diagnosis": { "id": 91, "misconception_id": 7,
                     "label": "Thinks GET is for any read-only form",
                     "question": "It looks like you…", "confirmed": null } },
    { "id": 311, "prompt": "…", "kind": "mcq", "options": ["…"], "gap_id": 486,
      "your_answer": null, "correct": null, "diagnosis": null }
  ]
}
```

* `your_answer` and `correct` are `null` together for an item not yet answered.
  Unlike the diagnostic, `correct` **is** returned here — practice already tells
  a student immediately whether they were right, so replaying it reveals
  nothing new.
* `diagnosis` is the same object `POST .../answer` returned, plus **`confirmed`**
  (`null` = asked but not answered, `true` = agreed, `false` = denied). A
  `confirmed: null` diagnosis is a question still waiting for the student —
  render it and the golden path survives a reload mid-flow.
* Only the **latest** attempt per item is reported.
* `explanation` and `citations` are **not** replayed. They cost a model call to
  produce and re-rendering yesterday's prose is not what resume is for; call
  `POST .../answer` again if the student re-answers.
* A set belonging to another student is `404 not_found`, not `403` — one
  student must not be able to discover that another's set exists.

> This endpoint is **read-only**. It writes no attempt, moves no mastery row and
> touches no teacher aggregate. Reading a pending diagnosis is not confirming
> it; only `POST /student/misconception-diagnosis/{id}/confirm` does that.

### Misconception check — `student-006`
The answer response carries the diagnosis when the answer is wrong:
```json
{
  "correct": false,
  "correct_answer": "12 N",
  "explanation": "…",
  "citations": [ /* Citation */ ],
  "diagnosis": {
    "id": 91,
    "misconception_id": 7,
    "label": "Treats velocity as implying a net force",
    "question": "It looks like you assumed constant velocity means there's a net force. Does that match your thinking?"
  }
}
```
`diagnosis` is `null` when the answer is correct or no known error pattern matches.

`POST /student/misconception-diagnosis/{diagnosis_id}/confirm` — body `{ "confirmed": true }` → `204`.

> **Only `confirmed: true` feeds the teacher heatmap.** Denied diagnoses are stored but excluded from every teacher aggregate.

### Tutor — `rag-003`, `rag-004`, `i18n-001`

| Method | Path | Notes |
|---|---|---|
| `POST` | `/tutor/ask` | `{ question, language?, topic_id? }` → `TutorResponse` |
| `POST` | `/tutor/ask/stream` | SSE, **polish only — build after everything else** |

Branch on `outcome`: `answered` · `insufficient_evidence` · `graded_work_refused`. All three are `200`, not errors — a refusal is a successful, correct response.

SSE frames, if built: `event: token` with `data: {"text":"…"}`, then a final `event: done` carrying the complete `TutorResponse` (the alignment badge can only render after the stream ends, since the evidence check needs the full answer).

### Assigned reteach
`GET /student/assignments` → `{ items: [{ id, title, body, assigned_at, citations }] }`. Only teacher-approved units appear here. **Built `teacher-006`.** `citations[]` is empty: a unit's citations are gathered when it is drafted and there is no column to keep them in, so the student gets the teacher-approved prose without invented sources. `assigned_at` is read from the approval audit row.

---

## Teacher

> Every teacher response is **anonymized**: no `student_id`, no name, no email, in any field. Verify this in the API payload, not just the rendered UI.

### Misconception heatmap — `teacher-001`
`GET /teacher/misconceptions/heatmap?course_id=3&topic_id=12`
```json
{ "topic": "Newton's Laws", "class_size": 40, "updated_at": "2026-08-23T12:02:00Z",
  "items": [ { "misconception_id": 7, "label": "Treats velocity as implying a net force",
               "confirmed_count": 14, "share": 0.35, "problem_type": "newtons-second-law" } ] }
```
Ranked by `confirmed_count` desc. Frontend **polls** this (suggested 5s while the demo is live).

### Reasoning-path breakdown — `teacher-002`
`GET /teacher/problems/{problem_type}/reasoning-paths`
```json
{ "items": [ { "misconception_id": 7, "label": "…", "confirmed_count": 14,
               "example": { "given_answer": "24 N", "reasoning": "…" } } ] }
```

### Prerequisite gap map — `teacher-003`
`GET /teacher/gap-map?course_id=3&topic_id=12`
```json
{ "items": [ { "concept": "Vector components", "prerequisite_course": "Class 12 Physics",
               "students_missing": 11, "share": 0.275 } ] }
```

### Uncertainty flags — `teacher-004`
| Method | Path | Notes |
|---|---|---|
| `GET` | `/teacher/uncertainty-flags` | `?status=open` |
| `POST` | `/teacher/uncertainty-flags/{id}/resolve` | `{ note? }` → `204` |

```json
{ "id": 55, "question": "Explain Lagrangian mechanics", "alignment_percent": 11,
  "reason": "no_matching_material", "topic_id": 12, "occurred_at": "…", "status": "open" }
```
Rows are written automatically by `rag-003`. No separate wiring.

### Before/after tracking — `teacher-005`
`GET /teacher/misconceptions/{misconception_id}/before-after`
```json
{ "misconception_id": 7, "label": "…",
  "before": { "window": "…", "confirmed_count": 14, "share": 0.35 },
  "after":  { "window": "…", "confirmed_count": 5,  "share": 0.125 },
  "reteach_at": "2026-08-23T10:00:00Z", "delta_share": -0.225 }
```
`after` is `null` when no reteach has happened yet.

`after` also carries `attempts_in_window` and `measured`. **`delta_share` is
`null` until `measured` is true**, with a `note` saying why. A reteach approved
a minute ago has zero confirmations after it, which would otherwise divide into
a share of zero and subtract into a flattering negative delta — while nobody
has actually been asked. Zero evidence and zero occurrences are not the same
measurement.

### Auto-suggested reteach — `teacher-006`
| Method | Path | Notes |
|---|---|---|
| `GET` | `/teacher/reteach` | `?status=draft` — **added after the freeze.** Without it there is no way to reach a unit that already exists: `suggest` returns one once and `PATCH` needs an id, so a reloaded page lost it. |
| `POST` | `/teacher/reteach/suggest` | `{ misconception_id }` **or** `{ concept_id }` — exactly one. → `ReteachUnit` (`status: "draft"`) |
| `POST` | `/teacher/reteach/suggest-top` | Drafts the top three of each ranking in one call. **`teacher-008`.** |
| `PATCH` | `/teacher/reteach/{id}` | `{ title?, body? }` |
| `POST` | `/teacher/reteach/{id}/approve` | → `status: "assigned"` |

```json
// ReteachUnit
{ "id": 12, "misconception_id": 7, "concept_id": null, "target": "misconception",
  "label": "Puts the foreign key on the one side of a one-to-many relationship",
  "title": "…", "body": "…",
  "practice_items": [ /* PracticeItem */ ], "citations": [ /* Citation */ ],
  "status": "draft", "approved_by": null }
```

#### A unit targets a misconception **or** a prerequisite concept — `teacher-008`

`misconception_id` is nullable as of `teacher-008`, and `concept_id` is new.
**Exactly one of the two is set**, and `target` says which (`"misconception"` |
`"concept"`) so a frontend never has to infer it from a null.

The two kinds are not the same lesson with a different key on it:

* A **misconception** unit argues against a belief the class already holds and
  that has been working for them. It names the wrong model, finds the case
  where it breaks, and says what to notice next time.
* A **concept** unit teaches a prerequisite they were never taught. There is no
  wrong model to dislodge — arguing against one they do not hold is confusing,
  so it gets its own prompt (`prompts/reteach_prerequisite.md`).

`practice_items[]` is empty for a concept unit. They are found through
`problem_type`, which is a property of a misconception; a prerequisite gap has
no error pattern to exercise yet.

> A `draft` unit is **never** visible at `GET /student/assignments`. Enforced by the query, which filters `status == "assigned"`. The approval gate is the human-in-the-loop story — never auto-assign.

`PATCH` on an **approved** unit is `409 conflict`. Otherwise what a teacher
approved and what students received could differ with nothing recording that
they diverged; un-approve and re-approve leaves two audit rows instead.

`suggest` returns `422 insufficient_evidence` when the approved corpus cannot
support a unit on that misconception — an unsupported unit becomes invented
content wearing a teacher's name the moment it is approved. The response also
carries `evidence` (the same `EvidenceReport` as a lesson) and `citations[]`.
`practice_items[]` never include `correct_answer`; a teacher-facing screen is
still a screen.

#### Drafting the whole panel at once — `teacher-008`

`POST /teacher/reteach/suggest-top` — no body. Fills the panel from **both**
rankings: three units from `GET /teacher/misconceptions/heatmap` and three from
`GET /teacher/gap-map`, so a teacher opening the page finds it populated rather
than facing six deliberate button presses.

**It aims for three from each ranking, not literally the top three rows.** A row
that yields no unit — the corpus refuses it, or a gap is already covered by a
misconception unit — advances to the next candidate instead of consuming a
slot. Taken literally, "the top three" produced **two** units against the real
corpus: one refusal and two overlaps, every one of them a correct decision, and
still an empty-looking screen. A row that already *has* a unit does consume a
slot, because the panel shows it.

It looks at most `8` rows deep per ranking, so a thin corpus cannot turn one
press into forty model calls.

```json
{
  "created": [ /* ReteachUnit */ ],
  "skipped": [
    { "target": "misconception", "id": 16, "label": "…",
      "reason": "insufficient_evidence", "alignment_percent": 41 },
    { "target": "concept", "id": 19, "label": "Filtering and querying records",
      "reason": "already_drafted", "unit_id": 14 },
    { "target": "concept", "id": 18, "label": "One-to-many relationships",
      "reason": "covered_by_misconception", "unit_id": 12 }
  ],
  "coverage": { "requested_per_ranking": 3, "from_heatmap": 3, "from_gap_map": 2 }
}
```

`coverage` says how many slots each ranking actually filled. Below
`requested_per_ranking` means the corpus could not support more — not that the
endpoint gave up early.

Everything it makes is a `draft`. **It never assigns**, so `GET
/student/assignments` is unchanged by this call — the approval gate is the
whole human-in-the-loop story and a batch button must not become a way around
it.

`skipped[].reason` is one of:

| `reason` | Meaning |
|---|---|
| `insufficient_evidence` | The corpus cannot support a unit on that target. Carries `alignment_percent`. **The other five are still drafted** — one refusal must never fail the batch. |
| `already_drafted` | An unapproved draft for that target already exists. Running this twice does not double the units; use `suggest` to redraft one. |
| `already_assigned` | An approved unit already covers it. Not silently replaced — that would change what students were given. |
| `covered_by_misconception` | A gap concept whose error pattern a misconception unit in this same batch already covers. The top gap and the top heatmap row are frequently the same subject seen from two directions, and two near-identical units read as padding. |

A `503` from the provider chain fails only the target it was drafting; the
batch reports it as `provider_unavailable` and carries on. The endpoint returns
`200`, not `201` — it is a partial-success report, not a single creation.

### AI-sourced content verification queue — `teacher-007`
| Method | Path | Notes |
|---|---|---|
| `GET` | `/teacher/verification-queue` | `?status=pending` |
| `POST` | `/teacher/verification-queue/{id}/approve` | → `status: "approved"` |
| `POST` | `/teacher/verification-queue/{id}/reject` | `{ reason? }` |

```json
{ "id": 3, "source_url": "https://…", "title": "…", "excerpt": "…",
  "found_for_gap": "Lagrangian mechanics", "status": "pending", "found_at": "…" }
```

> `pending` items must be unreachable from every student endpoint. Items are **seeded** for this build — no live web search is implemented.

---

## Features with no HTTP surface

Documented here so nobody goes looking for an endpoint that was never meant to exist.

| Feature | Where it lives |
|---|---|
| `infra-001` shared database | `.env` `DATABASE_URL` + `backend/scripts/check_db.py` |
| `infra-003` this contract | this file |
| `infra-005` tunnel | `cloudflared` + `VITE_API_BASE` in `frontend/.env.local` |
| `a11y-001` accessibility | client-side only — see below |
| `auth-002` forgot password | client-side only, deliberately no route |
| `demo-001` rehearsal | `docs/demo-script.md` |

---

## Accessibility — `a11y-001`

**Almost no endpoints.** Font size and high contrast are client-side state, and the only other server involvement is `preferred_language` on `User`.

**Read-aloud must use `TutorResponse.speech_text`, not `body`.** `body` is markdown, and read aloud its citation markers become spoken numbers — "…returns model instances when executed **four**" — while `**bold**` and backticks are noise or odd pauses depending on the engine. `speech_text` is the same answer with the markdown removed and the citation markers dropped; the citations themselves are still in `citations[]` and still on screen. It is present on **every** `TutorResponse`, including both refusals, and is built from the translated body, so a Hindi answer is spoken in Hindi.

```js
speechSynthesis.speak(new SpeechSynthesisUtterance(response.speech_text))
```

---

## Language handling — `i18n-001`

Send `language` on `/tutor/ask` and `/student/gaps/{id}/lesson`, or rely on `User.preferred_language`. **Built `i18n-001`.** Omitting it uses the saved preference; `language` means *the language the student wants to read in*, and the inbound translation **auto-detects** what they actually typed rather than assuming it matches. Supported: `en` `hi` `bn` `ta` `te` `mr`; anything else falls back to English rather than erroring.

`language` in the **response** is the language actually produced, not the one requested. Translation can fail silently, and labelling English prose `hi` would claim something that did not happen. The server translates in, retrieves in English, answers in English, and translates out. **`citations[]` always references the English source book and page**, and `alignment_percent` is computed on the English text — so it does not drift between languages.

---

## What the frontend can mock today

Every shape above is final enough to mock. Suggested order, matching `feature_list.json` priority:

1. `POST /auth/login` → `{ token, user }`
2. `GET /student/course-summary`
3. `GET /student/diagnostic` → `POST /student/diagnostic/{id}/submit` → `{ gaps }`
4. `GET /student/gaps/{id}/lesson` → `TutorResponse` (mock all three `outcome` values)
5. `POST /student/practice/generate` → `POST .../answer` → `{ diagnosis }` → confirm
6. `GET /teacher/misconceptions/heatmap`

---

## Change log

| When | Change |
|---|---|
| 2026-08-24 | **`teacher-008` — a reteach unit can now target a prerequisite concept, not only a misconception.** `ReteachUnit.misconception_id` becomes **nullable**, `concept_id` is added, exactly one is set, and a new `target` field says which. New `POST /teacher/reteach/suggest-top` drafts the top three of the heatmap and the top three of the gap map in one call and reports what it skipped and why. `POST /teacher/reteach/suggest` now accepts `{ concept_id }` as well. Everything stays a `draft` — the batch never assigns. **This one needs a migration**: `create_all()` does not alter an existing table, so run `backend/scripts/migrate_reteach_targets.py` once against the shared database. |
| 2026-08-24 | **`student-009` — answers are now readable back, so a reload does not wipe them.** `GET /student/diagnostic` gains `submitted_at` and a `your_answer` on every item; new `GET /student/practice/{practice_set_id}` returns a set with `your_answer`, `correct` and the pending `diagnosis` (now carrying `confirmed`); `Gap` gains `latest_practice_set_id` so a client can find the set to resume. All additive — no existing field changed shape or meaning. The no-score rule is intact: diagnostic **correctness is still never stored**, only the answer text, so there remains nothing countable in the database and `correct_answer` still never leaves the server. |
| 2026-08-23 | Initial draft covering all 32 features. |
| 2026-08-23 | `/health` documented as always-200 with a `degraded` state; implemented in `infra-002`. |
| 2026-08-23 | Guardrail narrowed to `/tutor/ask` only, and now requires intent + assignment match. `Gap` gains `suggested_prompts`. |
| 2026-08-24 | Golden path complete. `POST /student/practice/generate` (needs `gap_id`; also returns `concept` and `source: generated\|seeded`), `POST /student/practice/{id}/answer`, `POST /student/misconception-diagnosis/{id}/confirm`, `GET /teacher/misconceptions/heatmap`, `GET /teacher/uncertainty-flags` and its `/resolve`. `student-004` Show Source needs no endpoint — it is the `Citation` object. |
| 2026-08-24 | **`TutorResponse` gains `speech_text`** (`a11y-001`, backend half). Read-aloud must use it instead of `body`: `body` is markdown, and `[4]` is spoken as "four" mid-sentence. Present on every outcome, including refusals. |
| 2026-08-24 | `i18n-001` built and verified live: Hindi in, Hindi out, identical citations and an identical alignment score. Response `language` now reports what was produced. Both routes fall back to `User.preferred_language` instead of defaulting to `en`. |
| 2026-08-24 | Admin built: `admin-002` departments/courses/prerequisites, `admin-001` material upload with archiving-not-deleting and version history, `admin-003` audit log. The `sourced_content` audit actions are the documented verbs (`.approve`/`.reject`), not the resulting status. The two ingest endpoints are marked NOT BUILT. |
| 2026-08-24 | Teacher panels built: `teacher-002` reasoning paths, `teacher-003` gap map, `teacher-005` before/after (now with `measured`/`attempts_in_window`; `delta_share` null until tested), `teacher-006` reteach suggest/patch/approve **plus new `GET /teacher/reteach`** and `GET /student/assignments`, `teacher-007` verification queue. |
| 2026-08-24 | `GET /student/mastery` is **now built** (`student-007`) — exact shape as documented; no aggregate score, no time-on-task, and nothing countable to rebuild one from. |
| 2026-08-24 | `POST /student/syllabus-upload` is **now built** (`student-008`) — PDF/`.txt`/`.md`, ≤10 MB, same `{gaps, message}` body as `submit`, `detected_from: "syllabus_upload"`, documented 400 reasons. |
| 2026-08-24 | `POST /tutor/ask` now returns `graded_work_refused` (`rag-004`). `GET /student/course-summary`, `GET /student/diagnostic`, `POST /student/diagnostic/{id}/submit`, `GET /student/gaps` and `GET /student/gaps/{id}/lesson` implemented. `diagnostic_id` **is the course id** — a course has exactly one diagnostic. `POST /student/syllabus-upload` is documented but **not built**. A resource `404` now keeps its own message instead of "No such route." |
| 2026-08-24 | `EvidenceReport.threshold` example corrected 0.35 → 0.68 (0.35 is below the embedding similarity floor, so refusal could never fire) and `reason` values documented. `POST /tutor/ask` implemented for `answered` and `insufficient_evidence`; `graded_work_refused` still pending `rag-004`. |
