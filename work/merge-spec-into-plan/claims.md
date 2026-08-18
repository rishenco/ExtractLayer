## C1
Claim: The spec skill does not exist, in the working tree or in git's index.
Evidence: `ls .claude/skills` lists `build`, `compound`, `plan`, `vision`. `git ls-files .claude/skills/spec` prints nothing.
Verify: `[ ! -e .claude/skills/spec ] && [ -z "$(git ls-files .claude/skills/spec)" ]`
Verdict:

## C2
Claim: `.claude/skills/plan/SKILL.md` specifies one document carrying Problem, Criteria, Not doing, Research, Approach, Steps and Risks, and instructs that the first three be shown to the human before research.
Evidence: `.claude/skills/plan/SKILL.md:30-51` is the template with all seven headings; `:15` reads "Write **Problem / Intent**, **Criteria** and **Not doing**, and show them to the human before you research."
Verify: `for s in Problem Criteria "Not doing" Research Approach Steps Risks; do grep -q "## .*$s" .claude/skills/plan/SKILL.md || exit 1; done; grep -q 'show them to the human before you research' .claude/skills/plan/SKILL.md`
Verdict:

## C3
Claim: The plan template gives acceptance criteria ids of the form `A1`, `/build` is instructed to tick them in `plan.md`, and all six criteria in this change's plan are ticked and carry a claim id.
Evidence: `.claude/skills/plan/SKILL.md:35` and `:56`; `.claude/skills/build/SKILL.md:45`; `work/merge-spec-into-plan/plan.md:13-18` are six `- [x] A<n> ... (C<n>)` lines.
Verify: `grep -q 'Criteria carry ids' .claude/skills/plan/SKILL.md && grep -q 'tick each acceptance criterion in .plan.md.' .claude/skills/build/SKILL.md && [ "$(grep -cE '^- \[x\] A[0-9]+ .*\(C[0-9]+\)$' work/merge-spec-into-plan/plan.md)" -eq 6 ]`
Verdict:

## C4
Claim: No markdown or shell file outside `work/` contains `/spec` or `spec.md`.
Evidence: the grep below prints nothing.
Verify: `! { grep -rn -e '/spec\b' -e 'spec\.md' --include='*.md' --include='*.sh' . | grep -v '^\./work/'; }`
Verdict:

## C5
Claim: `docs/lessons.md` no longer carries the lesson about an approved plan superseding a spec section.
Evidence: `docs/lessons.md` is 24 lines and the phrase is absent.
Verify: `! grep -q 'supersedes a spec section' docs/lessons.md`
Verdict:

## C6
Claim: `make check` passes on this tree.
Evidence: it prints `all gates pass` and exits 0.
Verify: `make check`
Verdict:
