# Generate practice for one gap

A student got this prerequisite concept wrong. Write practice questions that
target **that concept specifically** — not the course in general, and not a
neighbouring idea that happens to appear in the same chapter.

## What makes these questions different

Every wrong option must be a **mistake a real student actually makes**, not
filler. A distractor nobody would pick teaches nothing: the student rules it
out instantly and the question tests less than it appears to.

The known misconceptions for this concept are listed below, each with the
mistaken reasoning behind it. For each question:

- pick a `problem_type` from that list,
- work out what answer a student holding that misconception would arrive at,
- make that value one of the options, and
- record it in `distractors`, mapping the option text to the misconception slug.

That mapping is the point of the whole exercise. When the student picks that
option, they are told which specific piece of reasoning led them there — and
that only works if you say now which mistake you built each option from.

Do not map the correct answer to a misconception. Options not built from a
listed misconception can be left out of `distractors`, but at least one wrong
option must be in it.

## Rules

- Ground the physics or facts in the course material below. Numbers you invent
  must be consistent with how the material treats the topic.
- `kind` is `"mcq"`. Exactly four options, one correct.
- `correct_answer` must appear verbatim in `options`, and must be right.
- Options are short answer strings ("8.66 N", "0 N"), formatted alike, so no
  option stands out by shape.
- Vary the numbers and the setup between questions. Two questions that differ
  only in wording test one thing twice.
- `problem_type` must be copied exactly from the list below.

## Concept to practise

{{concept}}

## Known misconceptions for this concept

{{misconceptions}}

## Course material

{{context}}
