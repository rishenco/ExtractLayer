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

`CLAUDE.md` is capped at **500 words and 80 lines**, whichever binds first. It loads into every turn of every session, and selective ignoring sets in around 80 lines — past that, adding a rule costs you an existing one at random. The word cap is there so merging two rules into one long sentence cannot dodge the line cap.

A rule may be added only if:

- **Its trigger is an action, not a diagnosis.** The rule has to fire at a moment recognizable by what the agent is about to *do* — open a file, write a line, run a command, send a summary. Rules that first require noticing an abstract situation do not fire, because the agent never notices it is in that situation. Measured here: "fix causes at the layer that owns the concept" changed behavior in 0 of 6 trials on a task built to trigger it. The same intent aimed at an action — "when you are about to write the same coercion a second time, stop" — has a moment to fire at.
- **It is not default behavior.** If a capable agent already does this unprompted, it is not a rule, it is decoration. Verifying work is default; claiming more than the check covered is not.
- **It fits the cap.** If it does not, evict — and state what the evicted rule was for and why that is now safe to lose. Never evict by ranking rules "weakest": a rule that works silently generates no corrections and will always look weakest, so ranking evicts the best rules first.

Rules that survive these gates still only persuade. `CLAUDE.md` is delivered as an ordinary message and the model judges its relevance turn by turn, so a rule that must hold every time belongs in a hook, a lint, or a test — not in a fourth restatement here.

## 5. Propose, never apply

Show the diff and what it costs. The user approves. Rules that change themselves drift, and drift in the rules is worse than a missing rule.
