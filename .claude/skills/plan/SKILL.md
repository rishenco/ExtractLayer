---
name: plan
description: Judge the request, research the codebase, and write work/<slug>/plan.md for human approval. Use before any code is written.
argument-hint: "[what you want]"
---

This is the gate the human actually reviews. A wrong line here becomes hundreds of wrong lines of code, so spend the effort here rather than in the diff.

## Intent first

Read `docs/vision.md` and `docs/lessons.md`. If the request contradicts either, say so now. If it is the wrong solution to the problem behind it, name the problem you think they actually have and propose the alternative before writing anything. Then build what the human decides — a request you believed was wrong and built anyway is a defect you own.

Ask up to three questions, and only ones whose answers change what gets built. If the human is not reachable, every unasked question goes to **Risks & open**.

Write **Problem / Intent**, **Criteria** and **Not doing**, and show them to the human before you research. An approach aimed at the wrong problem is wasted, and a criterion is cheaper to argue about than a step.

## Research

Delegate to the `codebase-researcher` subagent. Do not run the searches yourself — its output is meant to arrive compact, and raw search results in this context are what make later steps sloppy. Split independent questions across parallel researchers. A plan written without research reads plausible and matches nothing in the repo; if research shows the intent half is not buildable as written, stop and say so rather than planning around it.

## Write

`work/<slug>/plan.md`, slug in kebab-case, under 150 lines:

```
# <title>

Status: Draft

## Problem / Intent
Who is blocked, on what, and how you know. Then what is different afterwards. Not the solution.
Objections: what you argued against in the request and what was decided. "None" is an answer.

## Criteria
- [ ] A1 <a statement that is true or false, provable by something that runs>

## Not doing
What this leaves alone. Include the adjacent thing someone will assume is included.

## Research
What is there now, from the researcher, as path:line. Facts only.

## Approach
The shape of the change in one paragraph, the layer it lands in and why not the neighbouring one, then each approach rejected and the reason it loses. At least one.

## Steps
1. <what changes> — files: path, path — proves it: <the command that fails before and
   passes after> (A1)

## Risks & open
What could go wrong and what makes it visible when it does. Each open question with the assumption taken meanwhile, and which way it is reversible.
```

## Rules

- Criteria carry ids — `A1`, `A2` — and every one maps to at least one step, named by id. `/build` ticks them here.
- A criterion no test, gate or command can settle is not a criterion. Rewrite it until one can, or move it to **Not doing**. "Works correctly", "is performant", "handles errors gracefully" are not criteria; three vague ones are worth less than one exact one.
- Every step names its files and the check that proves it — a step with no proof is a wish — and steps are ordered so the repo is working after each one, never only at the end.
- A new dependency, a schema change, or a boundary change in `docs/architecture.md` is an ADR in `docs/decisions/`, written as part of the step that needs it. An ADR argues from what the product needs now: its context is the constraint that forces the decision, never where the question came up. A reader holding only `docs/` must find it complete.
- Decisions are recorded as requirements — "X, because Y", never a transcript of who said what. **Objections** is the one line that keeps the argument itself.

## Review

Run the `plan-reviewer` subagent before you ask for approval. It judges the design: contracts, scale, reuse, responsibilities, and what the next capability in `docs/vision.md` costs on this shape. A wrong shape approved here is the most expensive thing this loop can produce.

Fix every blocking finding in the plan. A finding you do not take goes under **Risks & open** with the reason it loses, so the human approves knowing what was raised and declined.

No gate checks that this ran, so the record is the only trace: a plan that reached approval with nothing raised and nothing declined is one nobody attacked.

## Approval

Print **Criteria**, **Approach** and **Steps** and ask the human to approve. On approval, set `Status: Approved` in the file. `/build` refuses to run without it. If the human is not reachable, leave it Draft and stop — an unapproved plan is where the background loop is supposed to wait.
