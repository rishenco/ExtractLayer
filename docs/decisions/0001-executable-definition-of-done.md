# 0001. Executable definition of done

Date: 2026-08-14 Status: Accepted

## Context

Development runs largely through agents, in the background. An agent is a search process: with no objective function it wanders, and with a soft one it optimises for sounding correct. Review by a human on every diff does not scale and applies attention at the lowest-leverage point — a bad line of a plan becomes hundreds of bad lines of code.

Rubric-style self-assessment was rejected: a model scoring its own output on a numeric scale optimises the score, not the code.

## Decision

`make check` is the definition of done. It composes gates from `scripts/gates/`, each of which is a program that exits non-zero, plus each workspace's own linters, type checks and tests. CI runs the same command, so there is no weaker standard anywhere.

Model judgement is used only where execution cannot reach — intent, layering, readability — and is expressed as binary questions against written intent, never as a score.

Human attention sits at two gates: the plan, and the pull request.

Defects found after the fact close the hole that let them through, preferring a test, then a gate, then a hook, and only then prose.

## Consequences

Adding a workspace means declaring its checks and its layer boundaries before `make check` will pass, and a workspace whose tooling is not installed fails rather than skipping. An empty repository passes with a notice, which is the one case where nothing is being claimed.

Gates are the extension point. Growing the standard means adding a file to `scripts/gates/`, not editing a monolith. Each gate reads an injectable file list, so `05-selftest.sh` can prove it fires on violations and stays quiet on valid code — a gate with only a failing-direction test is how a gate silently stops working.

Repo-level gates are a floor, not a ceiling. They catch what a regex can catch reliably; per-language rules belong to the workspace linters, which parse rather than guess.

Rules that stay in prose are visible as debt in `docs/lessons.md` and against the `AGENTS.md` line cap, so the constitution cannot quietly grow into a document nobody reads.
