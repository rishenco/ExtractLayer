---
name: build
description: Execute an approved plan step by step, verify it, review it adversarially, and open a pull request. Use once work/<slug>/plan.md is Approved.
argument-hint: "[slug]"
---

Execute `work/<slug>/plan.md`. Nothing else.

## Refuse to start if

- `plan.md` is not `Status: Approved`. Say so and stop — do not ask to be allowed to proceed.
- The plan is stale: the files it names have changed since it was written. Re-run `/plan`.

## Execute

One step at a time, in order. For each step:

1. Make the change the step describes, and nothing the step does not describe.
2. Run the check the step named. It must fail before your change and pass after — if it
   passed before, the step proved nothing and needs a better check.
3. Run `make check`.
4. Append one line to the plan under the step: what you did, what you found.

Stop at the first step whose reality contradicts the plan. Say what the plan assumed and what
is actually true, and go back to `/plan`. Improvising past a wrong plan is how a change ends up
somewhere nobody chose.

When a step turns out to need something not in the plan, that is a finding, not a licence.
Small and inside the plan's intent: do it and note it. Anything else: stop and ask.

## Verify

- `make check` passes.
- Every acceptance criterion in `spec.md` is ticked, each next to the thing that proves it.
- `CHANGELOG.md` has the user-visible effect under `## [Unreleased]`.

## Review

Run the `adversarial-reviewer` subagent. Fix every blocking finding. For minor findings, fix or
record why not — in the pull request, not in a comment in the code.

Re-run `make check` after fixes. Then run `/compound` on anything the review found that could
recur elsewhere.

## Ship

Commit in the steps of the plan, not as one blob. Push to the branch and open a pull request
using the template. The body carries the plan link, the criteria with their evidence, the open
questions and assumptions taken, and what you chose not to do.

Then stop. The pull request is the second gate and it belongs to the human.
