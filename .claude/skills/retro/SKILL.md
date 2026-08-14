---
name: retro
description: Turn corrections from this session into durable project context. Use when the user redirected, rejected an approach, or clarified intent during a session, at the end of a substantial piece of work, or when invoked as /retro.
---

# Retro

A correction means context was missing. This decides where the missing context belongs.

Most corrections are missing **intent**, not missing **rules**. Routing them all into `CLAUDE.md` is how that file rots into noise that nothing obeys.

## 1. List the corrections

Every point where the user redirected, rejected, or clarified. Theirs only — not your own mid-task self-corrections. If there were none, say so and stop.

## 2. Route each one

| The correction was about | Where it goes |
|---|---|
| What we are building, for whom, what matters | `docs/vision.md` |
| A specific question, now answered | `docs/decisions.md`, one line |
| How this codebase works — a gotcha, a constraint | the code itself, or `docs/architecture.md` |
| How agents should behave, **and it has happened before** | `CLAUDE.md` |
| How agents should behave, first occurrence | nowhere |
| Taste on one artifact | nowhere |

First occurrences go nowhere on purpose. One mistake is noise; twice is a pattern. Rules written from single incidents are the main source of context bloat.

## 3. Spend the CLAUDE.md budget

`CLAUDE.md` is capped at 60 lines. It loads into every turn of every session, and instruction-following degrades as it grows — a rule added is attention taken from every rule already there.

A rule may be added only if:

- **It has a trigger.** A situation an agent can recognize. "Be careful with migrations" has none. "Before editing a migration, check whether it has already been applied" does.
- **It is not default behavior.** If a capable agent already does this unprompted, it is not a rule, it is decoration.
- **It fits the cap.** If it does not, name the weakest rule currently in the file and evict it, or do not add.

## 4. Propose, never apply

Show the diff and what it costs. The user approves. Rules that change themselves drift, and drift in the rules is worse than a missing rule.

If a rule was added and then violated anyway, stop proposing rules for it. Propose a hook, a lint, or a test — something that fails loudly. A rule that does not hold needs enforcement, not repetition.
