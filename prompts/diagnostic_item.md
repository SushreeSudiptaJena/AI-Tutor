# One prerequisite check

Write **one** multiple-choice question that finds out whether a student
arriving in this course already understands the concept below.

## What this question is for

This is a **prerequisite check, not an exam**. The student has not been taught
this here — the question is asking whether they bring it with them. A wrong
answer creates a gap and a remedial lesson; it is never a grade, and nobody is
ranked by it.

So the question must be answerable by someone who understands the *idea*, using
nothing but the idea. Not by someone who has memorised this book.

## Rules

- Exactly four options. One is right.
- **No option may depend on this book's running example.** A question only
  answerable if you remember the blog app in Chapter 1 tests recall of a
  tutorial, not understanding of a concept.
- Every wrong option must be a **mistake a real student makes**. A distractor
  nobody would pick teaches nothing and makes the question easier than it looks.
- Options are short, formatted alike, and none stands out by shape or length.
  The longest option must not be the correct one.
- No "all of the above", no "none of the above", no negations ("which is NOT").
- `correct_answer` must appear **verbatim** in `options`.
- Ground the question in the material below. Do not invent API behaviour.

## If the material cannot support a question

Return `"skip": true` and nothing else. That is a correct and expected answer —
the passage may describe an installation step, a file listing or a narrative
aside, none of which a student can be right or wrong about. **A weak question is
worse than no question**: it creates a gap the student does not have, and sends
them a remedial lesson for something they already understand.

## Concept

{{concept}}

## What it means

{{summary}}

## Material (pages {{pages}})

{{context}}
