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

## Claim

Write `work/<slug>/claims.md`, one block per claim, with a claim for every acceptance criterion
in the spec and one for `make check`:

```
## C1
Claim: a single sentence that is true or false
Evidence: what you observed, as command output or path:line
Verify: the exact command that settles it
Verdict:
```

Claim only what you observed. "`make check` passes" is a claim. "The code is correct" is not,
because nothing settles it — rewrite it until something does, or drop it. Do not write a claim
you already know nothing can check and hope it passes.

Never hedge a claim with a condition its `Verify:` command does not establish. "Passes once X"
cannot be refuted, which means it cannot be checked either.

Then tick each acceptance criterion in `spec.md` next to the claim that settles it, and put the
user-visible effect in `CHANGELOG.md` under `## [Unreleased]`.

## Audit

Run the `claim-auditor` subagent. It reproduces every claim from scratch and writes the
verdicts. It is not reviewing your code.

Do not argue with it. A claim it could not reproduce is withdrawn or made true — never
explained away. `75-claims.sh` fails while any verdict is `UNSUPPORTED`, `FALSE`, or missing.

## Review

Run the `adversarial-reviewer` subagent, separately, for the code itself: layer, shape,
correctness. Fix every blocking finding. For minor findings, fix or record why not — in the
pull request, not in a comment in the code.

Re-run `make check` after fixes. Then run `/compound` on anything either agent found that could
recur elsewhere.

## Ship

Commit in the steps of the plan, not as one blob. Push to the branch and open a pull request
using the template. The body carries the plan link, the criteria with their evidence, the open
questions and assumptions taken, and what you chose not to do.

Then stop. The pull request is the second gate and it belongs to the human.
