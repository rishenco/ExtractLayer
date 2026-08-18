---
name: spec
description: Turn an idea into work/<slug>/spec.md with checkable acceptance criteria. Use at the start of any change that could be built the wrong way.
argument-hint: "[what you want]"
---

Capture intent before anything is built. No code in this step.

## Before writing

Read `docs/vision.md` and `docs/lessons.md`. If the request contradicts either, say so now.

Judge the request itself. If it is the wrong solution to the problem behind it, name the problem you think they actually have and propose the alternative in one paragraph. Do this before writing the spec, not inside it. Then build what the human decides — but a request you believed was wrong and built anyway is a defect you own.

Ask up to three questions, and only ones whose answers change what gets built. If the human is not reachable, every unasked question goes to **Open questions**.

## Write

`work/<slug>/spec.md`, slug in kebab-case, under 80 lines:

```
# <title>

Status: Draft

## Problem
Who is blocked, on what, and how you know. Not the solution.

## Intent
What is different for the user afterwards. One paragraph.

## Acceptance criteria
- [ ] Each one a statement that is true or false, provable by something that runs.

## Non-goals
What this change deliberately leaves alone. Include the adjacent thing someone will
assume is included.

## Layer
Which layer from docs/architecture.md owns this, and why it is not the neighbouring one.

## Open questions
Each with the assumption taken in the meantime, and which way it is reversible.

## Objections
What you argued against and what was decided. "None" is an answer.
```

## Rules

- An acceptance criterion that cannot be proven by a test, a gate, or a command someone runs is not a criterion — rewrite it until it can be, or move it to Non-goals.
- "Works correctly", "is performant", "handles errors gracefully" are not criteria.
- Three vague criteria are worth less than one exact one.
- A spec records decisions as requirements — "X, because Y", never a transcript of who said what or when. **Objections** is the one section that keeps the argument itself.
- Do not describe implementation. That is `/plan`.

End by telling the human the spec is ready and what you need from them. Then `/plan <slug>`.
