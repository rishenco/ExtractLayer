---
name: retro
description: Turn corrections from this session into durable project context. Use when the user redirected, rejected an approach, or clarified intent during a session, at the end of a substantial piece of work, or when invoked as /retro.
---

# Retro

A correction means context was missing. This decides where the missing context belongs.

Most corrections are missing **intent**, not missing **rules**. Routing them all into `CLAUDE.md` is how that file rots into noise that nothing obeys.

## 1. Read the corrections

`docs/corrections.md` is the record. Add anything from this session that is not in it yet, then work from the file — not from memory of the transcript. If it is empty, say so and stop.

## 2. Ask first: is this already covered?

Search `CLAUDE.md`, `docs/vision.md`, and `docs/decisions.md` for a line that already says it.

If one exists, the correction is a **violation**, not a gap. Adding a second rule beside the ignored one is the bloat mechanism this skill exists to prevent. The only legal routes are:

- propose enforcement — a hook, a lint, a test, something that fails loudly
- nothing

Never both a rule and its restatement.

## 3. Route what is left

| The correction was about | Where it goes |
|---|---|
| What we are building, for whom, what matters | `docs/vision.md` |
| A question now answered, where a different answer would have changed the build | `docs/decisions.md`, one line |
| How this codebase works — a gotcha, a constraint | the code itself |
| How agents should behave, **and `corrections.md` shows it before** | `CLAUDE.md` |
| How agents should behave, first occurrence | nowhere — it stays logged, that is enough |
| Taste on one artifact | nowhere |

If a new decision resolves something `docs/vision.md` lists as an open tension, delete the tension. An open question that has been answered is worse than no note at all.

## 4. Spend the CLAUDE.md budget

`CLAUDE.md` is capped at **600 words**. It loads into every turn of every session, and instruction-following degrades as it grows — a rule added is attention taken from every rule already there. The cap is words, not lines, so that merging two rules into one long sentence is not a way to dodge it.

A rule may be added only if:

- **It has a trigger.** A situation an agent can recognize. "Be careful with migrations" has none. "Before editing a migration, check whether it has already been applied" does.
- **It is not default behavior.** If a capable agent already does this unprompted, it is not a rule, it is decoration.
- **It fits the cap.** If it does not, evict — and state what the evicted rule was for and why that is now safe to lose. Never evict by ranking rules "weakest": a rule that works silently generates no corrections and will always look weakest, so ranking evicts the best rules first.

## 5. Propose, never apply

Show the diff and what it costs. The user approves. Rules that change themselves drift, and drift in the rules is worse than a missing rule.
