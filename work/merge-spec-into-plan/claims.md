## C1
Claim: The spec skill does not exist, in the working tree or in git's index.
Evidence: `ls .claude/skills` lists `build`, `compound`, `plan`, `vision`. `git ls-files .claude/skills/spec` prints nothing.
Verify: `[ ! -e .claude/skills/spec ] && [ -z "$(git ls-files .claude/skills/spec)" ]`
Verdict: SUPPORTED
Ran `[ ! -e .claude/skills/spec ] && [ -z "$(git ls-files .claude/skills/spec)" ]` -> exit 0; `ls .claude/skills` prints build, compound, plan, vision, and `git ls-files .claude/skills/spec` prints nothing; recreating the directory makes the same command exit 1.

## C2
Claim: `.claude/skills/plan/SKILL.md` specifies one document carrying Problem, Criteria, Not doing, Research, Approach, Steps and Risks, and instructs that the first three be shown to the human before research.
Evidence: `.claude/skills/plan/SKILL.md:30-51` is the template with all seven headings; `:15` reads "Write **Problem / Intent**, **Criteria** and **Not doing**, and show them to the human before you research."
Verify: `for s in Problem Criteria "Not doing" Research Approach Steps Risks; do grep -q "## .*$s" .claude/skills/plan/SKILL.md || exit 1; done; grep -q 'show them to the human before you research' .claude/skills/plan/SKILL.md`
Verdict: SUPPORTED
Ran the heading loop -> exit 0 and `grep -q 'show them to the human before you research'` -> exit 0; the seven headings sit inside the template fence at `.claude/skills/plan/SKILL.md:30,34,37,40,43,46,50` and the quoted sentence is line 15 verbatim; renaming `## Criteria` makes the loop exit 1.

## C3
Claim: The plan template gives acceptance criteria ids of the form `A1`, `/build` is instructed to tick them in `plan.md`, and all six criteria in this change's plan are ticked and carry a claim id.
Evidence: `.claude/skills/plan/SKILL.md:35` and `:56`; `.claude/skills/build/SKILL.md:45`; `work/merge-spec-into-plan/plan.md:13-18` are six `- [x] A<n> ... (C<n>)` lines.
Verify: `grep -q 'Criteria carry ids' .claude/skills/plan/SKILL.md && grep -q 'tick each acceptance criterion in .plan.md.' .claude/skills/build/SKILL.md && [ "$(grep -cE '^- \[x\] A[0-9]+ .*\(C[0-9]+\)$' work/merge-spec-into-plan/plan.md)" -eq 6 ]`
Verdict: SUPPORTED
Ran the compound command -> exit 0: `Criteria carry ids` at `.claude/skills/plan/SKILL.md:56`, the `- [ ] A1` template line at `:35`, the tick instruction at `.claude/skills/build/SKILL.md:45`, and six ticked lines at `work/merge-spec-into-plan/plan.md:13-18`; unticking A1 drops the count to 5 and the command exits 1.

## C4
Claim: No markdown or shell file outside `work/` contains `/spec` or `spec.md`.
Evidence: the grep below prints nothing.
Verify: `! { grep -rn -e '/spec\b' -e 'spec\.md' --include='*.md' --include='*.sh' . | grep -v '^\./work/'; }`
Verdict: SUPPORTED
Ran the grep -> no output, exit 0; `git grep -nI -i spec` over every tracked file of any extension hits `/spec` and `spec.md` only under `work/merge-spec-into-plan/`; appending `Run /spec first.` to `README.md` makes the command exit 1.

## C5
Claim: `docs/lessons.md` no longer carries the lesson about an approved plan superseding a spec section.
Evidence: the phrase is absent from the file.
Verify: `! grep -q 'supersedes a spec section' docs/lessons.md`
Verdict: SUPPORTED
Ran `! grep -q 'supersedes a spec section' docs/lessons.md` -> exit 0; `git show 86d46dc -- docs/lessons.md` is that one line deleted; appending the phrase back makes the command exit 1.

## C6
Claim: `make check` passes on this tree.
Evidence: it prints `all gates pass` and exits 0.
Verify: `make check`
Verdict: SUPPORTED
Ran `make check` twice: on the tree as received, with the C9 and C11 verdicts blank, it printed `FAIL 75-claims` / `work/merge-spec-into-plan/claims.md: 11 claims but 9 verdicts` and exited 2; with all eleven verdicts recorded it prints `all gates pass` and exits 0, every other gate reporting `ok` on both runs.

## C7
Claim: `CHANGELOG.md` describes the loop as plan → build → compound with one approved document per change, and names no spec anywhere.
Evidence: `CHANGELOG.md:10`.
Verify: `grep -q 'plan → build → compound loop' CHANGELOG.md && grep -q 'one approved document per change' CHANGELOG.md && ! grep -qi spec CHANGELOG.md`
Verdict: SUPPORTED
Ran the compound command -> exit 0; `CHANGELOG.md:10` carries both phrases and `grep -ni spec CHANGELOG.md` prints nothing; appending a `spec` line makes the command exit 1.

## C8
Claim: `make check` now exercises `.claude/hooks/session-start.sh`, and fails if the hook reports a slug that has no plan.
Evidence: `scripts/gates/05-selftest.sh:290-306`. With the `[ -f "$dir/plan.md" ] || continue` guard replaced by a branch that prints, the selftest reports "session hook: reports a slug with no plan as open work" and exits 1.
Verify: `grep -q 'session-start.sh' scripts/gates/05-selftest.sh && ./scripts/gates/05-selftest.sh`
Verdict: SUPPORTED
Ran `grep -q 'session-start.sh' scripts/gates/05-selftest.sh && ./scripts/gates/05-selftest.sh` -> exit 0, and `make check` reports `ok 05-selftest`, so the gate that reads the hook runs; replacing the `[ -f "$dir/plan.md" ] || continue` guard with a branch that prints made the selftest print `session hook: reports a slug with no plan as open work` plus `session hook: does not print exactly one state per slug` and exit 1. The hook block is `scripts/gates/05-selftest.sh:292-309`, not the cited `:290-306`.

## C9
Claim: `README.md` names `work/<slug>/` as holding a plan and claims, `work/README.md` lists both files, the reviewer reads a plan only if one exists, and the plan template asks why the layer is not the neighbouring one.
Evidence: `README.md:33`, `work/README.md:6-7`, `.claude/agents/adversarial-reviewer.md:10`, `.claude/skills/plan/SKILL.md:44`.
Verify: `grep -q 'plan and claims for one change' README.md && grep -q 'claims.md' work/README.md && grep -q 'if one exists' .claude/agents/adversarial-reviewer.md && grep -q 'why not the neighbouring one' .claude/skills/plan/SKILL.md`
Verdict: SUPPORTED
Ran the four-part grep -> exit 0: the layout line `work/<slug>/      plan and claims for one change` is the phrase's only occurrence and sits at `README.md:32`, not the cited `:33`, which is the `scripts/gates/` line; `work/README.md:6-7` name `plan.md` and `claims.md`; `.claude/agents/adversarial-reviewer.md:10` reads the plan `if one exists`; `.claude/skills/plan/SKILL.md:44` asks why not the neighbouring layer; rewording each of the four in turn makes the command exit 1.

## C10
Claim: `docs/lessons.md` carries a rule on checking a layout block against its directory's README, and a rule on diffing a repointed reader clause by clause.
Evidence: `docs/lessons.md:24-25`.
Verify: `[ "$(grep -cE "layout block naming a directory's contents|rename repoints a reader" docs/lessons.md)" -eq 2 ]`
Verdict: SUPPORTED
Ran the count -> 2, exit 0, matching `docs/lessons.md:24-25`; deleting line 25 drops the count to 1 and the test exits 1.

## C11
Claim: `.claude/agents/adversarial-reviewer.md` tells the reviewer how to judge a change that ships with no plan; `work/merge-spec-into-plan/plan.md` carries one outcome note under each of its seven steps, and one correction under the research bullet it retracts.
Evidence: `.claude/agents/adversarial-reviewer.md:10`; the seven `- Done:` lines under the steps and the `- Correction from the build:` line under Research in `work/merge-spec-into-plan/plan.md`.
Verify: `grep -q 'Skips-plan-gate' .claude/agents/adversarial-reviewer.md && [ "$(grep -c '^   - Done:' work/merge-spec-into-plan/plan.md)" -eq 7 ] && [ "$(grep -c '^  - Correction from the build:' work/merge-spec-into-plan/plan.md)" -eq 1 ]`
Verdict:
