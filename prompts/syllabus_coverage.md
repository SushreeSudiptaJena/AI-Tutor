# Syllabus coverage check

An incoming student has given us the syllabus of what they have **already
studied** — a previous course, a previous institution, a prior semester. Below
that is the list of prerequisite concepts their **new** course assumes they
arrive with.

For each prerequisite, decide one thing: **does this syllabus show the student
has already been taught it?**

## What counts as covered

Wording will not match. A syllabus is a list of unit titles written by somebody
else, so judge by meaning, not by keyword:

- "Unit 3 — Object-oriented programming in Python: classes, inheritance,
  polymorphism" covers *Class inheritance in Python*.
- "Web technologies: client-server model, request methods, status codes"
  covers *The HTTP request and response cycle* and *HTTP methods, GET and POST*.
- "Database Management Systems: ER modelling, keys, normalisation" covers
  *Primary keys and foreign keys*.

A concept counts as covered when the syllabus teaches it directly, or teaches
something that plainly contains it. A passing mention in a course title is not
enough — "Advanced Python" on its own does not tell you inheritance was taught.

## The bias, and why

**When it is genuinely unclear, answer `false` — not covered.**

These are not symmetric mistakes, and the asymmetry runs the opposite way to
most judgement calls in this system.

Wrongly saying **covered** hides a real gap. The student is never offered the
lesson they needed, nobody finds out, and the first sign of trouble is that
they cannot follow the course. The whole point of this upload is to find those
gaps; a false `true` defeats it silently.

Wrongly saying **not covered** offers a student a short lesson on something
they already know. They skip it. That is a mild annoyance, and it is visible —
they can see the gap is wrong, which a hidden gap never is.

So: no evidence in the syllabus means `false`. Do not give the student the
benefit of the doubt; give it to the gap.

`evidence` is the phrase from the syllabus that convinced you, quoted, when the
answer is `true`. Leave it empty when the answer is `false` — there is nothing
to quote.

## The prerequisite concepts

{{concepts}}

## The syllabus the student uploaded

{{syllabus}}
