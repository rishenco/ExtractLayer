---
name: compound
description: Turn a defect or review finding into a check that fails the build next time. Use after any review, bug fix, or moment a rule had to be stated by hand.
argument-hint: "[what went wrong]"
---

A defect that only gets fixed will happen again in a different file. Close the hole, not the
instance.

## Locate the hole

State in one sentence what the system believed that was wrong, and which gate should have
caught it but did not. If every existing gate would legitimately have passed, the hole is a
missing gate.

## Close it

Take the first option that genuinely fits. Do not skip down the list because a lower one is
faster to write.

1. **A test.** The behaviour was wrong. Add the case that fails before the fix.
2. **A gate** in `scripts/gates/`, or a rule in the workspace linter or boundary config. The
   shape was wrong and a program can see it. Prefer configuring a linter already here over a
   new script.
3. **A hook** in `.claude/hooks/`. The mistake happens during work and is worth catching at the
   moment it is made rather than at the end.
4. **A line in `docs/lessons.md`.** Only when the first three genuinely cannot see it.
   Imperative, one line, naming the change that taught it.

## Rules

- A new gate ships with a case in `scripts/gates/05-selftest.sh` proving it fires, and one
  proving it does not fire on legitimate code. A gate with no false-positive case will be
  disabled by the first person it annoys.
- Run `make check` on the whole repo before committing a new gate. If it fails on existing
  code, either the code is wrong or the gate is — decide which, out loud.
- Never weaken a gate to make a change pass. Change the code, or change the rule deliberately
  with an ADR saying why.
- Adding to `AGENTS.md` is the last resort and it is capped. At the cap, merge or delete a rule
  rather than growing the file. Prose does not fail the build.

## Report

One line: what would now fail, and where. If the answer is "a human would have to notice", you
picked option 4 too early — go back up the list.
