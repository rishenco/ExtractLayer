---
name: plan
description: Research the codebase and write work/<slug>/plan.md for human approval. Use after /spec and before any code is written.
argument-hint: "[slug]"
---

This is the gate the human actually reviews. A wrong line here becomes hundreds of wrong lines of code, so spend the effort here rather than in the diff.

## Research first

Delegate to the `codebase-researcher` subagent. Do not run the searches yourself — its output is meant to arrive compact, and raw search results in this context are what make later steps sloppy. Split independent questions across parallel researchers.

A plan written without research reads plausible and matches nothing in the repo.

## Write

`work/<slug>/plan.md`, under 150 lines:

```
# <title>

Status: Draft

## Research
What is there now, from the researcher, as path:line. Facts only.

## Approach
The shape of the change in one paragraph, and the layer it lands in.

## Rejected
Approaches considered and the reason each loses. At least one.

## Steps
1. <what changes> — files: path, path — proves it: <the command or test that fails before
   and passes after>
2. ...

## Risks
What could go wrong, and what makes it visible when it does.

## Not doing
Things a reader would expect here that are out of scope.
```

## Rules

- Every step names its files and the check that proves it. A step with no proof is a wish.
- Every acceptance criterion in the spec maps to at least one step. Say which.
- Steps are ordered so the repo is working after each one, never only at the end.
- If the plan needs a new dependency, a schema change, or a boundary change in `docs/architecture.md`, that is an ADR in `docs/decisions/` — write it as part of this step.
- An ADR argues from what the product needs now. Its context is the constraint that forces the decision — never the story of what the repo used to do or where the question came up. A reader holding only `docs/` must find it complete.
- If research showed the spec is not buildable as written, stop and say so. Do not plan around a broken spec.

## Approval

Print the **Approach**, **Rejected** and **Steps** sections and ask the human to approve. On approval, set `Status: Approved` in the file. `/build` refuses to run without it.

If the human is not reachable, leave it Draft and stop. An unapproved plan is where the background loop is supposed to wait.
