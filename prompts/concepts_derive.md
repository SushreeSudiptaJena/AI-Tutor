# Read a syllabus out of the book

Below is a continuous run of text from one chapter of a course textbook, with
the pages it came from. Name the **teachable concepts** this passage
introduces — the things a student would have to understand, each of which a
tutor could build one lesson around.

## What counts as a concept

A concept is a **named idea a student can be right or wrong about**. It is what
you would put on a syllabus line, not what you would put in an index.

Good: "Model field types and their database columns", "The request–response
cycle", "Template inheritance with blocks".

Not concepts:

- **A specific API call, flag or filename.** `reverse_lazy()` is not a concept;
  "URL reversing" is. `settings.py` is not a concept; "project configuration"
  might be.
- **A step in the book's running example.** "Creating the blog app" is what the
  chapter *does*, not what it *teaches*. The concept underneath it is
  "Django applications and project structure".
- **A heading with no content behind it.** If the passage only mentions
  something in passing, leave it out. A concept with nothing to teach produces
  a lesson that refuses.
- **Two concepts glued together.** "Models and migrations" is two lines, not
  one.

## How many

Most passages of this length introduce **one to three** concepts. Some
introduce none — a page of installation commands, a table of contents, a
chapter summary that only restates. **Returning an empty list is a correct
answer** and is much better than inventing something to fill the slot.

## `prerequisite`

Ask one question, and only this one:

> **Would a student who passed {{prerequisite_course}} already know this,
> before ever opening this book?**

If yes — `prerequisite: true`. If it is specific to **{{subject}}**, `false`.

Do **not** ask whether the book explains it. The book explains everything in
it; that is what a book is. A chapter that opens by reminding you what a Python
class is has not made Python classes part of this course's syllabus.

`true` — general programming and computing knowledge this book *uses*:

- Python syntax, functions, classes, inheritance, exceptions
- What HTTP is, what a request and a response are, GET versus POST
- What a database table, a row, a column and a primary key are
- HTML elements, forms and input fields
- The shell, file paths, installing packages

`false` — anything belonging to **{{subject}}** itself: its APIs, its
conventions, its project layout, its own abstractions, the way *it* does a
thing that other tools also do.

Both answers are common. A chapter of pure {{subject}} material yields no
prerequisites at all, and that is a correct result — but a passage explaining
Python classes yields one even though it sits in this book.

## Rules

- `name` is a noun phrase, 3–8 words, no trailing punctuation, and readable on
  its own away from this passage. Never start it with "How to" or "Introduction
  to".
- `summary` is **one sentence** saying what the concept is. Not what the
  passage says about it — what it *is*.
- Both must be grounded in the passage below. Do not add concepts you know
  belong to this subject but which this text does not introduce.

## Chapter

{{chapter}}

## Pages {{pages}}

{{context}}
