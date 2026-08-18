---
name: vision
description: Interview the human and write docs/vision.md. Use when product intent is missing, stale, or when agents keep guessing what the product should be.
argument-hint: "[topic to revisit, optional]"
disable-model-invocation: true
---

Write `docs/vision.md` from the human's answers. You are interviewing, not drafting.

## Interview

Ask **one question at a time** and wait. Never batch them, never answer for them, never fill a gap with something plausible. An unanswered question goes to **Open** in the document.

Work through these, skipping any already answered in `docs/vision.md`:

1. In one sentence, what does ExtractLayer do, and for whom?
2. What do those people do today instead? What is bad about it?
3. Who is explicitly not the user, even though they look like one?
4. What must always be true about this product — the constraint you would reject a popular feature over?
5. What must it never become? Describe the version of this you would hate to have built.
6. Twelve months out, what is true that is not true today? What single number tells you it worked?
7. What is the riskiest assumption you are making?
8. What are you deliberately not building first, and why that order?

Then one on taste: name a product whose feel you want, and one you want to avoid. Ask why in each case — the reason is the reusable part, not the name.

When an answer is vague, probe once, concretely: ask for an example, a user, or a number. Do not probe twice; record what you got.

## Write

`docs/vision.md`, under 200 lines, in the human's own words wherever they were specific:

```
# Vision
What it is            one paragraph, their sentence
Who it is for         and who it is not for
The job it replaces   what people do today
Always true           constraints that override feature requests
Never                 what this must not become
Twelve months         the outcome and the number
Riskiest assumption   and what would disprove it
Not building first    and the reason for the order
Taste                 the feel we want, the feel we avoid
Open                  questions the human has not answered yet
```

Any answer that constrains how the system is built, rather than what it does, becomes an ADR in `docs/decisions/` instead — vision holds product intent, decisions hold engineering commitments.

Update the first line of `README.md` to their one-sentence answer, and log the change in `CHANGELOG.md`. The README and the vision describe the product, never the repository's condition at a moment in time — a phase, a rewrite in progress, a not-yet-built state goes under **Open** or nowhere.

Finish by reading back only the **Always true**, **Never** and **Open** sections and asking whether they are right. Those three are what future agents will refuse work over.
