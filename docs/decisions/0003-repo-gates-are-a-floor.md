# 0003. Repo-level content gates are a floor, replaced by real linters

Date: 2026-08-14 Status: Accepted

## Context

`10-comments`, `20-budgets` and `30-slop` are regexes over lines. They exist because the repo has no workspace yet and therefore no linter, and something had to hold the line on comments, size and filler from the first commit.

They are also wrong in ways a regex is always wrong. Adversarial review found the comment gate both missing real comments and rejecting valid code across two rounds; it still cannot see that a `#` sits inside a heredoc or a Go raw string, because it matches one line at a time. `eslint`, `ruff`, `golangci-lint` and `vale` parse instead of guessing, are maintained, and already encode these rules.

Reinventing a maintained tool is the failure this repo's own rules name at `AGENTS.md:32`. Keeping the floor forever would be that failure.

## Decision

The repo-level content gates are a floor with a defined end. A workspace that configures its own linter is no longer scanned by them: `el_drop_linted` removes its paths from `10-comments`, `20-budgets` and `30-slop`. The prose phrase list is retired by deleting it from the gate once a Vale style covers the same ground — a config file does not stand in for a check that runs.

`55-lint-config.sh` makes the handoff a hard requirement rather than an intention. It fails once any workspace exists without its linter configured, naming the rules that must replace the floor.

The floor is deleted outright when every workspace is linted and Vale is in place. Until then it covers only what nothing else covers.

## Consequences

The first workspace commit costs more: it must bring an eslint, ruff or golangci config and a Vale style with it. That is the point — it is the moment the real tools become available, and the moment the floor's false positives would otherwise become permanent.

Coverage recedes automatically rather than by anyone remembering, so the two systems never run against the same file and disagree.
