# ExtractLayer — Operating Rules

Open-source SaaS. UI: TypeScript/React. Backend: undecided (see `docs/decisions/0002-backend-stack.md`).

| Where intent lives | File |
| --- | --- |
| What we build and refuse to build | `docs/vision.md` (run `/vision` if missing) |
| Layers and the dependency rule | `docs/architecture.md` |
| Decisions and their reasons | `docs/decisions/` |
| Rules that could not be made executable | `docs/lessons.md` |

## Definition of done

`make check` passes. Nothing else counts — not "it compiles", not "looks right".

A claim about the code that `make check` cannot verify is either made verifiable or not
claimed. New behaviour ships with the check that proves it.

## The loop

`/spec` → `/plan` → **human approves** → `/build` → claim audit → code review → PR →
**human approves** → `/compound`

Claims about the work are separate from the work. `/build` writes `work/<slug>/claims.md`, the
`claim-auditor` subagent reproduces each claim from scratch, and `scripts/gates/75-claims.sh`
fails on any verdict that is `UNSUPPORTED`, `FALSE`, or missing. An agent's word is not
evidence, including your own.

`scripts/gates/70-approved-plan.sh` checks it: a branch that changes source needs a
`work/<slug>/plan.md` marked `Status: Approved`. Setting that line yourself is forgery, not a
shortcut — the gate makes intent traceable, and the pull request review is what enforces it.

Skip only for changes that cannot be wrong in an interesting way — typos, a single-line fix
already covered by a test, dependency bumps — by putting `Skips-plan-gate: <reason>` in the
commit that touches the file. Skipping is allowed; skipping silently is not.

## Intent

- Build what the spec says. Not the adjacent thing, not the general version of it.
- Ambiguity is not an input to guess from. Resolve it in this order: check `docs/`, ask the
  human if reachable, otherwise record it under **Open questions** in the spec, take the
  smallest reversible option, and surface it in the PR body.
- A request you believe is wrong gets challenged before it gets built. Say what is wrong,
  propose the alternative, then proceed with the human's answer. Building something you
  judged to be a mistake is a defect, not obedience. Record the objection and the answer in
  the spec — an objection nobody can find later is one that stops being raised.
- Unrequested scope is a defect. Refactors, renames, and "while I was in there" fixes belong
  in their own change.

## Shape of the code

- Fix causes at the layer that owns them. A fix at a different layer than its cause is a
  workaround — label it as one and propose the real fix.
- Abstractions earn their place with a second real caller. Not an imagined one.
- Deleting is a valid change. Prefer it.
- No code comments. Exceptions: directives (`//nolint`, `# noqa`, `// @ts-expect-error`) and
  one line above an algorithm a competent reader would misread.
- Write what a careful human would write. If it reads as generated, it is wrong.
- Lean on the dependencies already here before adding one, and on well-maintained libraries
  before writing your own. Check the docs and types before concluding a library can't do it.

## Shape of the writing

- Short and declarative. State what is true, not the path you took to it.
- No reasoning-in-progress in committed text. Docs and code are the source of truth, not a
  draft of your thinking.
- Every user-visible change updates `CHANGELOG.md` under `## [Unreleased]`.

## Growing the system

Start from the smallest version that works end to end. Add each capability on top of a
product that already works. Never trade a working product for unfinished complexity.
Architectural decisions are made for the long term; a stopgap meant to be replaced later is
not accepted — it gets an ADR or it does not get built.

## Compounding

Every defect that survives to review is a hole in the gate, not just a bug. Close the hole in
this order, stopping at the first that applies:

1. A test.
2. A rule in `scripts/gates/` or the workspace linter.
3. A hook in `.claude/hooks/`.
4. One line in `docs/lessons.md`.

Prose is the last resort because prose does not fail the build.

## This file

Capped at 120 lines, enforced by `scripts/gates/20-budgets.sh`. At the cap, adding a rule
means merging or deleting one. Rules here are the ones that could not be made executable —
that is a debt, not a feature.
