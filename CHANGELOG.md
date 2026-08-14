# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Operating rules in `AGENTS.md`, with `CLAUDE.md` as a thin Claude-specific layer.
- `make check` as the single definition of done, composed of gates in `scripts/gates/`:
  code comments, size budgets, slop markers, changelog freshness, architecture boundaries,
  and per-workspace checks.
- Agent loop as skills: `/vision`, `/spec`, `/plan`, `/build`, `/compound`.
- `codebase-researcher` and `adversarial-reviewer` subagents.
- Hooks that enforce the rules instructions can only request: session briefing, post-edit
  comment feedback, and a stop gate that blocks finishing on a red `make check`.
- CI running the same `make check` as local, plus a PR template carrying the plan link and
  acceptance criteria.
- `docs/architecture.md` layer map, `docs/decisions/` records, `docs/lessons.md`.
- `scripts/gates/70-approved-plan.sh`: source changes must trace to a human-approved plan, or
  carry a `Skips-plan-gate:` trailer that records the skip.

- `scripts/gates/55-lint-config.sh`: a workspace must configure its own linter, and the
  repo-level content gates stop scanning it once it does. Recorded in
  `docs/decisions/0003-repo-gates-are-a-floor.md`.
- `docs/working.md`: how to run the development process efficiently.

### Fixed

- Boundary and linter config checks accepted a workspace only when every filename variant
  existed, so a correctly configured workspace could never pass.
- The stop gate stopped checking once work was committed, which is how `/build` ends.
- Comment detection missed trailing, inline and JSX comments while rejecting arithmetic
  continuations, TypeScript private fields and Go build tags. Markers are now per language,
  string literals are stripped first, and the gate is scoped as a floor under the workspace
  linters rather than a replacement for them.
- Paths containing non-ASCII characters were silently excluded from every content gate.
- Python and Go workspaces passed silently when their tooling was absent.
- `EL_FILE_LIST` could disable every gate; `check.sh` now clears it and refuses to run without
  the selftest.
- `vendor/`, `dist/` and `node_modules/` were only skipped at the repository root.
- Filler detection missed typographic apostrophes.
- CHANGELOG.md was subject to a 200-line budget it must eventually exceed.
- A `Skips-plan-gate:` trailer exempted the whole branch and every branch descended from it,
  leaving the plan gate inert. It now exempts only the files touched by the commit that
  carries it, and never uncommitted changes.
- The plan gate accepted any `plan.md` anywhere, and any line beginning `Status: Approved`.
  It now requires `work/<slug>/plan.md` and an exact status line.
- `40-changelog` and `70-approved-plan` silently passed without a base ref, so a shallow clone
  disabled both. They now fail with the fetch depth to fix.
- The stop gate skipped its check entirely when no base ref existed, allowing a stop on red.
- Comment detection mangled regex literals when stripping escapes, and a directive word
  anywhere on a line exempted the whole line. Directives must now follow a comment marker.
- Workspace discovery treated a `package.json` under `work/` or `docs/` as a real workspace.
- A Go workspace with no `.go` files failed `go vet`, blocking the first incremental commit.
- The post-edit hook read the last `file_path` in the payload rather than the edited one.
