# Demo script — `demo-001`

> **Owner:** person 6 presents; Sushree runs the backend laptop.
> Drafted by the backend owner from the verified behaviour, because the script
> has to match what the code actually does. **Person 6 owns the words** — rewrite
> the narration freely, but do not change the *sequence* without re-rehearsing:
> every step below is one that has been run end to end and recorded under
> `evidence/`.

The demo course is **CSW2 — Computer Science Workshop 2 (Django)**. Not physics.
Every citation opens a real page of a real ingested textbook.

---

## Before you start

| | |
|---|---|
| **Laptop A** | Student. Browser at the tunnel URL. Logged out. |
| **Laptop B** | Teacher dashboard, on the misconception heatmap, **already loaded**. |
| **Backend** | Sushree's machine: `RUN_START_COMMAND=1 ./init.sh`, then `./tunnel.sh`. |
| **Accounts** | `asha@example.edu` / `demo1234` · `ravi@example.edu` / `demo1234` · `admin@example.edu` / `demo1234` |

**Run this first, every time:**

```bash
.venv/Scripts/python.exe backend/scripts/reset_demo_state.py
```

It clears what a rehearsal leaves behind and re-seeds the class history, so the
heatmap is populated but not repetitive. It does **not** touch chunks — that
would cost ~40 minutes of re-embedding. Never run `reset_db.py` on demo day.

**Then rehearse the exact path below at least once while online.** This is not
superstition: see *If the wifi dies* at the end.

---

## The golden path — 4 minutes

### 1. The student arrives · Laptop A
Log in as **asha@example.edu**. The course summary names *Computer Science
Workshop 2* and the book behind it, *Django 5 By Example*.

> "Everything this tutor says comes out of that one book. Watch what happens
> when I ask it something the book doesn't cover."

### 2. The prerequisite diagnostic
Open the diagnostic. Eight questions, each testing something a fourth-semester
student is assumed to arrive with from CSW1.

**Answer them all correctly except *"A form creates a new blog post when it is
submitted. Which HTTP method should it use?"* — choose *"GET, because it is a
simpler request."***

> "No score comes back. That's deliberate — the output is a **gap list**, not a
> grade. The problem statement asks what a student is missing, not how they rank."

One gap: **HTTP methods, GET and POST**, attributed to **Computer Science
Workshop 1**.

> "It doesn't just say she's weak on this. It says *which earlier course this
> should have come from*. That's the difference between 'reteach it' and 'the
> prior course has a problem'."

### 3. The lesson, with its alignment score
Open the gap. A lesson appears with an **alignment badge** and citations to
real pages of the Django book.

> "That percentage is not the model's confidence. It's a top-k cosine match
> against the approved corpus **plus** a separate entailment check. And these
> citations resolve — page numbers in a book that exists."

Click **Show Source** on one citation.

### 4. Practice scoped to the gap
Generate practice. Every item is about choosing an HTTP method — not general
Django trivia.

### 5. The moment · answer wrong
Answer the enrol-button question with **GET**.

The tutor does not just mark it wrong. It says:

> *"That answer usually comes from this reasoning: chooses GET for a request
> that changes server state. Does that match your thinking?"*

> "It's not telling her she's wrong. It's telling her **why** she's wrong, and
> then asking whether that's actually what she thought — because a diagnosis
> she doesn't recognise is worse than no diagnosis."

### 6. Confirm · **both laptops on screen now**
Tap **Yes, that was my thinking**.

**Laptop B — the teacher's heatmap — moves from 7 to 8.**

> "One student confirmed a misconception, and the teacher's dashboard now shows
> eight students holding it. Nothing was wired between those two screens: the
> student's confirmation *is* the teacher's data."

### 7. Say the part that matters
> "Only **confirmed** diagnoses count. If she'd said 'no, that's not what I
> thought', it would be stored and excluded — so the number on a teacher's
> screen means *students who agreed*, not *times the algorithm guessed*."

---

## The three rubric features — 2 minutes

### Refuse when there's no evidence
Ask the tutor: **"Who won the football world cup in 2018?"**

It refuses, and says it has flagged it. Switch to **Laptop B → Uncertainty
Flags**: the question is there.

> "One feature, two dashboards. Every refusal becomes a teacher's to-do item,
> automatically."

### The graded-work guardrail
Paste a question **copied verbatim out of Assignment 1**.

It declines to solve it — and offers scaffolded hints instead.

> "Two independent signals have to fire: it matches graded material *and* an
> intent check says she wants the answer rather than the understanding. Ask the
> same question as 'why does this need a custom manager?' and it teaches you.
> Wanting to understand your homework is legitimate tutoring."

### Answer in Hindi
Ask a Django question in **Hindi**.

> "Answer in Hindi. **Same citations, same pages, same alignment score** — we
> translate at the edges and retrieve in English, so the badge doesn't drift
> between languages."

---

## The teacher's half — 2 minutes · Laptop B

- **Reasoning paths** — not just *how many* got it wrong, but *how*.
- **Gap map** — which prerequisites this class arrived without, and from which course.
- **Reteach unit** — press suggest. A draft appears, grounded in the corpus.
  **Point at the word `draft`.**

> "It will not reach a single student until Ravi approves it. That's the whole
> human-in-the-loop story — and if the corpus can't support a unit, it refuses
> to write one rather than inventing something with his name on it."

Approve it. It appears on the student's assignments.

- **Before/after** — the panel that can say the intervention *didn't* work.

> "And before anyone has actually been retested, it says so instead of showing
> a flattering zero."

---

## Close

> "36 hours. One book, ingested and page-anchored. Every answer traceable to a
> page, every refusal traceable to a teacher's queue, and every claim about a
> student confirmed by that student before a teacher ever sees it."

---

## If it goes wrong

| Symptom | Do this |
|---|---|
| Bare tunnel URL shows `{"error":{"code":"not_found"...}}` | **Nothing is broken.** There is no `GET /` route. Use `/health`. |
| Routes 404 but `/health` is 200 | A stale uvicorn owns port 8000. Kill it and restart. |
| Heatmap looks repetitive | `reset_demo_state.py`. |
| Practice generation is slow | It is one LLM call. Rehearsed paths are cached and instant. |
| A judge asks for a brand-new gap | It will work, but it will take a few seconds. Say so. |

### If the wifi dies

Set `PROVIDER=mock` and keep going. **The rehearsed path still works fully** —
including the misconception moment — because the disk cache is keyed on
`sha256(model + prompt)` and replays the real answers.

**But only the rehearsed path.** An unrehearsed question falls through to the
mock provider, which answers with a visible `[offline placeholder]` telling you
exactly that. It deliberately asserts no subject matter of its own — a mock that
invents confident prose under real citations is worse than one that admits what
it is.

**So: rehearse the exact questions above, verbatim, while online.** That is what
puts them in the cache.

---

## Verification status

`demo-001` is **not passing** and cannot be closed by one person. Its four
steps need two laptops and a second operator:

1. Laptop A student flow, Laptop B teacher dashboard — *needs a second person*
2. Run this script verbatim end to end — *needs both laptops*
3. Repeat from a clean state with no manual DB edits — *needs both laptops*
4. Repeat with wifi disabled and `PROVIDER=mock` — **the backend half of this
   has been run and recorded** (`evidence/demo-001/offline-mock-run.txt`); the
   two-laptop repeat has not

Budget the last three hours for this. Do not spend them on features.
