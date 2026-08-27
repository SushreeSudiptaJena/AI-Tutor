# Follow-up rewrite

A student is in an ongoing tutoring conversation. Their newest message may
depend on what was said earlier — "explain that more simply", "why?", "and for
a ManyToMany?" — and it is about to be sent to a retrieval system that sees
**only the message**, with no memory of the conversation at all.

Your job is to rewrite that message into a **standalone question**: one that
means the same thing to someone who has not read the conversation.

## Rules

**Resolve references using the conversation, and nothing else.** Pronouns and
deictics — *that, it, this, they, those, the same, again* — get replaced with
the thing they actually refer to, taken from the earlier turns. So after an
answer about model managers, "explain that more simply" becomes "Explain model
managers more simply."

**Never add detail the conversation does not contain.** Do not guess the
subject, do not add examples, do not make the question more specific than the
student made it. If the reference is genuinely ambiguous, prefer the most
recent topic; if even that is unclear, return the message unchanged.

**Preserve what kind of question it is.** "Why?" stays a why-question.
"Explain that more simply" keeps *more simply* — the student is asking for a
different treatment, not a different topic. Keep the student's own wording
wherever it still makes sense; you are filling in a missing noun, not writing
a better question.

**Leave a standalone message alone.** Most messages need nothing done to them.
"What is a QuerySet?" is already complete — return it exactly as it is and set
`rewritten` to false. A message that merely *mentions* a pronoun is not
automatically incomplete: "What is a QuerySet and when should I use it?"
resolves its own "it" and needs no help.

**Do not answer the question.** You are only rewriting it. Do not add
commentary, do not explain your reasoning in `standalone`, and do not turn a
question into a statement.

**Length.** A standalone question should be one sentence. If your rewrite runs
much longer than the student's message plus the missing noun, you are adding
detail — go back and add less.

## Why this matters

The rewritten question is what gets searched against the course textbook, and
it is also what the graded-work guardrail inspects. Adding subject matter the
student never asked about makes the tutor answer a question nobody asked, and
makes the alignment score describe the wrong thing. Under-resolving is safe:
the pipeline behaves exactly as it does today. Over-resolving is not.

## Output

`standalone` — the rewritten question, or the original message verbatim.
`rewritten` — true only if you actually changed it.

## The conversation so far, oldest first

{{history}}

## The student's newest message

{{question}}
