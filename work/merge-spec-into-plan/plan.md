# Merge the spec into the plan

Status: Draft

## Problem / Intent

Two documents describe one change. No gate reads `spec.md`: `scripts/gates/70-approved-plan.sh` and `scripts/gates/75-claims.sh` name `plan.md` and `claims.md` only, so the spec carries a review cost and no enforcement. The split has already produced drift, recorded as a lesson in `docs/lessons.md:15`. Afterwards a change carries one document, approved once, with acceptance criteria that carry ids a later gate can match against claim ids.

Objections: none.

## Criteria

- [ ] A1 `/spec` is gone: `.claude/skills/spec/` does not exist.
- [ ] A2 `/plan` writes one document holding problem, criteria, not-doing, research, approach, steps and risks, and shows the intent half to the human before the approach half exists.
- [ ] A3 Acceptance criteria carry ids (`A1`, `A2`, ...) and `/build` ticks them in `plan.md`.
- [ ] A4 Outside `work/`, nothing names `/spec` or `spec.md`.
- [ ] A5 The lesson at `docs/lessons.md:15` is gone, its failure class being impossible.
- [ ] A6 `make check` passes.

## Not doing

- Deleting `docs/working.md`, capping `docs/lessons.md`, tiering the loop by change size.
- The gate matching criterion ids against claim ids. The ids land here so that gate becomes writable; the gate is its own change.
- Widening `EL_CODE_EXT` so prompt files need a plan and a ledger.

## Research

- `scripts/gates/70-approved-plan.sh:19-24` matches `work/*/plan.md` and greps `^Status:[[:space:]]*Approved$`. `scripts/gates/75-claims.sh:24-30` collects `work/*/claims.md`. Neither names `spec.md`.
- `scripts/gates/05-selftest.sh:207-236` asserts exit codes of `70-approved-plan.sh`, never its message, so the message is free to change.
- `/spec` or `spec.md` is named at: `README.md:10`, `CLAUDE.md:5`, `AGENTS.md:17`, `docs/working.md:5`, `scripts/gates/70-approved-plan.sh:36`, `.claude/skills/spec/SKILL.md`, `.claude/skills/plan/SKILL.md:3`, `.claude/skills/build/SKILL.md:45`, `.claude/agents/adversarial-reviewer.md:10`, `.claude/agents/claim-auditor.md:34`, `.claude/hooks/session-start.sh:5` and `:14`, `work/README.md:6`, `.github/pull_request_template.md:5`.
- `.claude/hooks/session-start.sh:13-17` reports a slug as `spec only, no plan`, a state that stops existing.
- `work/` has no slug directories, so no historical record is rewritten.

## Approach

One document at `work/<slug>/plan.md`, written by `/plan` in two passes: problem, criteria and not-doing first, shown to the human, then research, approach and steps. One `Status:` line, one approval. The path does not move, so `70-approved-plan.sh` and `75-claims.sh` are untouched. `/spec` is deleted and its readers point at the single document.

Rejected — keeping both files and adding a consistency check between them: it pays a gate to maintain a split nothing enforces. Rejected — merging into `spec.md`: the two gates name `plan.md`, so renaming costs gate and selftest edits for nothing. Rejected — keeping `/spec` as an alias onto the merged document: two entry points for one artifact is the same drift moved.

## Steps

1. Rewrite `.claude/skills/plan/SKILL.md` as the merged skill: the template, criterion ids, the two-pass interaction, the approval rule — files: `.claude/skills/plan/SKILL.md` — proves it: `for s in Problem Criteria "Not doing" Research Approach Steps Risks; do grep -q "## .*$s" .claude/skills/plan/SKILL.md || exit 1; done` (A2, A3)
2. Delete the spec skill — files: `.claude/skills/spec/SKILL.md` — proves it: `[ ! -e .claude/skills/spec ]` (A1)
3. Move the loop line and the skill list — files: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/working.md`, `.claude/hooks/session-start.sh`, `scripts/gates/70-approved-plan.sh` — proves it: `! grep -rn '/spec\b' --include='*.md' --include='*.sh' . | grep -v '^./work/'` (A4)
4. Move the artifact readers onto `plan.md` — files: `.claude/skills/build/SKILL.md`, `.claude/agents/adversarial-reviewer.md`, `.claude/agents/claim-auditor.md`, `work/README.md`, `.github/pull_request_template.md` — proves it: `! grep -rn 'spec\.md' --include='*.md' --include='*.sh' . | grep -v '^./work/'` (A4)
5. Drop the `spec only, no plan` branch from the session hook — files: `.claude/hooks/session-start.sh` — proves it: `./scripts/gates/05-selftest.sh` passes and the hook prints one state per slug (A4)
6. Delete the drift lesson — files: `docs/lessons.md` — proves it: `! grep -q 'supersedes a spec section' docs/lessons.md` (A5)
7. Run the whole check — proves it: `make check` (A6)

## Risks & open

- The merged skill grows past one screen and the two-pass interaction gets skipped in practice. Visible as file length: the skill stays at or under the 67 lines it holds now.
- A reader of a merged pull request loses the intent-only view that the spec gave. Visible in the pull request body, which keeps criteria and their evidence as separate sections.
- Open: whether `docs/working.md` survives at all. Assumption taken: it stays, amended. Reversible by deleting it later, since nothing imports it.
