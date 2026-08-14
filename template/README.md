# Agent context template

Drop-in context for a codebase written mostly by agents. Language-agnostic; nothing here is specific to a product.

## Install

Copy `CLAUDE.md`, `docs/`, and `.claude/skills/retro/` into the repo root. Edit line 1 of `CLAUDE.md`. Fill in `docs/vision.md`. That is the whole setup.

## How it holds together

`CLAUDE.md` holds two different things, and the first matters more.

**Facts** are what an agent cannot infer and will otherwise waste a session guessing: the test command, which package owns what, which directories are generated. This is pure information gain — it does not have to persuade anyone, so it never fails to land. Surveyed public files (opencode, Sentry, Cloudflare, Next.js, Supabase) spend roughly **60–65% of their length here**. Fill this in first; it is the highest-value thing in the file.

**Behavior** is how the agent works. It is weaker than it looks — the model judges each rule's relevance turn by turn — so it stays short and every rule earns its slot.

`docs/vision.md` and `docs/decisions.md` are intent — what to build and what is already settled. Most of what you would otherwise write as rules is really missing intent, and putting intent in the rules file is what turns it into noise nothing obeys.

`docs/corrections.md` plus `/retro` is the loop. Corrections are logged when they happen; `/retro` decides which file each belongs in, and refuses most of them.

## Rules for the rules

Three things that measurably matter, in order:

1. **No contradictions.** Two rules that fight cancel each other. The largest single improvement measured while building this came from noticing that "don't touch files the task didn't name" was blocking "settle the value at its source" — agents found the duplication and then declined to fix it. Naming the exception took the outcome from 0/3 to 3/3.
2. **Trigger on an action, not a diagnosis.** A rule fires at a moment recognizable by what the agent is about to *do* — open a file, write a line, claim done. Rules that first require noticing an abstract situation do not fire, because the agent never notices it is in one.
3. **Cut anything already default.** Agents ran their own tests unprompted in every trial, so "run your tests" was pure decoration. What they did *not* do by default was keep their claims inside what those tests covered.

Keep the behavior half under ~80 lines. Past roughly that, adding a rule costs you an existing one at random. Facts are cheaper per line than rules — they are looked up, not obeyed — but the same budget eventually applies.

When a project outgrows one file, do what the large repos do: keep the root file short and scope the rest by subtree (`src/AGENTS.md`, `frontend/AGENTS.md`) or point at a per-package doc, so a session loads only what its work touches.

## What this cannot do

`CLAUDE.md` is delivered as an ordinary message, and the model judges its relevance turn by turn. It persuades; it does not enforce. An invariant that must hold *every* time belongs in a hook, a lint, or a test. `/retro` routes must-hold rules there instead of writing a fourth restatement of one already being ignored.
