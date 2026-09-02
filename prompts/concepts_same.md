# Is this concept already on the list?

A new concept was read out of a textbook. Below it are the existing concepts
whose names are closest to it. Decide whether the new one is **the same
teachable concept** as one of them, said differently.

## The test

Two names are the same concept when **one lesson would teach both**. Not when
they are about the same technology, not when they appear on the same page — when
a student who understood one has, by that fact, understood the other.

Same concept:

- "Python virtual environments" / "Virtual environments and package isolation"
- "URL routing" / "Mapping URLs to views"

Different concepts, however similar the words:

- "Django project file structure" / "Django project settings" — one is where
  files live, the other is what configures the project. Two lessons.
- "Model fields" / "Model relationships" — both about models, taught separately.
- "Writing a template" / "Template inheritance" — the second builds on the
  first, which means they are not the same.

**When the two would need separate lessons, they are different.** Say `null`.
A wrong merge silently deletes a concept from the syllabus and nobody finds
out; a wrong split leaves a near-duplicate that a human can see and remove.
Prefer the visible mistake.

## Answer

Return the `slug` of the existing concept the new one duplicates, or `null` if
it is genuinely new.

## The new concept

{{candidate}}

## Existing concepts

{{existing}}
