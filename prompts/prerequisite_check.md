# Second opinion: is this really a prerequisite?

A concept was read out of **{{book}}** and marked as knowledge a student should
already have from **{{prerequisite_course}}**, rather than something this course
teaches. Check that.

## The question

> Could this concept be taught in full **without naming anything specific to the
> subject of {{book}}**?

**Yes → `true`.** It is general programming or computing knowledge. The book
happens to use it.

- "Class inheritance and method overriding" — plain object-oriented programming.
- "HTTP request methods" — true of every web system ever built.
- "Installing packages with pip" — the Python packaging tool, used everywhere.
- "Primary keys in a relational table" — database basics.

**No → `false`.** The concept, *as named*, is about this book's own subject —
its classes, modules, settings, commands, decorators, project layout, or its
own name for a general idea.

- "Installing Django using pip" — pip is general, but this concept is about
  setting up the very thing the course teaches.
- "Defining model field choices with TextChoices" — an enumeration idea wearing
  a framework-specific class name.
- "The MTV architectural pattern" — this framework's own name for MVC.

## The tie-break

Judge the concept **as it is named**. If stripping the subject's vocabulary out
of the name would leave a real, general concept behind, it is `true` and the
name is just decorated. If stripping it leaves nothing, it is `false`.

Both answers are normal, and a concept that reads as ordinary programming
knowledge should not be rejected merely for appearing in this book — the book
uses a great deal that it does not teach.

## The concept

name: {{concept}}

summary: {{summary}}
