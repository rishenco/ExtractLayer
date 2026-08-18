## C1
Claim: `.claude/skills/reconcile/SKILL.md` exists and its frontmatter description says when to run the skill.
Evidence: `.claude/skills/reconcile/SKILL.md:3` reads "Use when the written record has drifted from the code, or before planning from a document nobody has checked lately."
Verify: `[ -f .claude/skills/reconcile/SKILL.md ] && sed -n '1,5p' .claude/skills/reconcile/SKILL.md | grep -q '^description: .*Use when'`
Verdict: SUPPORTED
Ran the two-part test -> exit 0; line 3 is the description and reads "Use when the written record has drifted from the code, or before planning from a document nobody has checked lately." verbatim; rewriting `Use when` as `It runs when` in a copy makes the same grep exit 1.

## C2
Claim: The skill's first two bash blocks, run verbatim against this tree, print three lines whose tokens are exactly `add_pairs`, `assign_split` and `derived_values`.
Evidence: the two blocks at `.claude/skills/reconcile/SKILL.md:11-14` and `:20-31` print `docs/lessons.md:14: assign_split`, `docs/lessons.md:20: add_pairs` and `docs/lessons.md:20: derived_values`, and nothing else.
Verify: `[ "$(awk '/^```bash$/{n++;f=1;next} /^```$/{f=0} f && n<=2' .claude/skills/reconcile/SKILL.md | bash | awk '{print $NF}' | sort | tr '\n' ' ')" = "add_pairs assign_split derived_values " ]`
Verdict: SUPPORTED
Ran the extraction into `bash` -> exit 0; the blocks at `:11-14` and `:20-31` print `docs/lessons.md:14: assign_split`, `docs/lessons.md:20: add_pairs`, `docs/lessons.md:20: derived_values` and nothing else; a fourth dangling token planted in a new `docs/` file appears in the output and makes the command exit 1.

## C3
Claim: The skill states a five-entry precedence ladder for the canonical home of a duplicated rule, and states that every losing copy becomes a pointer to the winner rather than being deleted.
Evidence: `.claude/skills/reconcile/SKILL.md:61` introduces the ladder, `:63-67` are its five entries, and `:69` reads "Every losing copy becomes a pointer to the winner."
Verify: `grep -q 'The canonical home is the first of these that can hold the rule' .claude/skills/reconcile/SKILL.md && [ "$(grep -cE '^[1-5]\. ' .claude/skills/reconcile/SKILL.md)" -eq 5 ] && grep -q 'becomes a pointer to the winner' .claude/skills/reconcile/SKILL.md`
Verdict: SUPPORTED
Ran the three-part grep -> exit 0: the ladder opener at `:61`, five entries matching `^[1-5]. ` at `:63-67`, and `:69` reading "Every losing copy becomes a pointer to the winner."; dropping entry 5 in a copy gives a count of 4, and rewording either sentence makes its grep exit 1.

## C4
Claim: The skill carries a "Do not flag" section of five entries and states that nothing under `work/` is edited.
Evidence: `.claude/skills/reconcile/SKILL.md:71-77` is the section with five bullets; `:81` reads "Nothing under `work/`."
Verify: `grep -q '^## Do not flag' .claude/skills/reconcile/SKILL.md && [ "$(awk '/^## Do not flag/{f=1;next} /^## /{f=0} f && /^- /' .claude/skills/reconcile/SKILL.md | wc -l)" -eq 5 ] && grep -q '^Nothing under `work/`' .claude/skills/reconcile/SKILL.md`
Verdict: SUPPORTED
Ran the three-part test -> exit 0: heading at `:71`, five bullets at `:73-77`, and `:81` opening "Nothing under" the `work/` path; deleting one bullet in a copy gives a count of 4 and rewording line 81 makes its grep exit 1.

## C5
Claim: The skill states that its citation scan reads identifiers only and that a citation carrying no identifier is invisible to it.
Evidence: `.claude/skills/reconcile/SKILL.md:35` reads "The scan reads identifiers only. A citation carrying no identifier — a component named in words alone — is invisible to it and rots the same way."
Verify: `grep -q 'The scan reads identifiers only' .claude/skills/reconcile/SKILL.md && grep -q 'A citation carrying no identifier' .claude/skills/reconcile/SKILL.md`
Verdict: SUPPORTED
Ran both greps -> exit 0, both matching line 35, which reads "The scan reads identifiers only. A citation carrying no identifier — a component named in words alone — is invisible to it and rots the same way."; rewording the first clause in a copy makes its grep exit 1.

## C6
Claim: `/reconcile` is named in `CLAUDE.md` and in `README.md`.
Evidence: `CLAUDE.md:6` and `README.md:13`.
Verify: `grep -q '/reconcile' CLAUDE.md && grep -q '/reconcile' README.md`
Verdict: SUPPORTED
Ran `grep -q '/reconcile' CLAUDE.md && grep -q '/reconcile' README.md` -> exit 0, matching `CLAUDE.md:6` and `README.md:13`, the only hits in either file; renaming the token in a copy of `README.md` makes it exit 1.

## C7
Claim: `make check` passes on this tree.
Evidence: it prints `all gates pass` across all 12 gates, `05-selftest` through `75-claims`.
Verify: `make check`
Verdict: SUPPORTED
Ran `make check` -> every gate `ok` from `05-selftest` to `75-claims`, twelve of them, then `all gates pass`, exit 0, with the nine verdicts written; on the same tree with any verdict line blank it exits 2 at `75-claims`, which reports `9 claims but 7 verdicts` for the two blanked last.

## C8
Claim: `CHANGELOG.md` carries one line under `## [Unreleased]` naming `/reconcile` and what it does.
Evidence: `CHANGELOG.md:11`, the last bullet of `### Added`, begins "- `/reconcile` checks the written record against the repo".
Verify: `[ "$(awk '/^## \[Unreleased\]/{f=1} f && /^- .*\/reconcile/' CHANGELOG.md | wc -l)" -eq 1 ]`
Verdict: SUPPORTED
Ran the awk-and-count test -> exit 0; `CHANGELOG.md:11` is the last bullet of `### Added` under `## [Unreleased]` and begins "- `/reconcile` checks the written record against the repo"; deleting the bullet, duplicating it, or moving it above the `## [Unreleased]` heading each makes the command exit 1.

## C9
Claim: All seven acceptance criteria in `work/reconcile-skill/plan.md` are ticked and each names the claim that settles it.
Evidence: `work/reconcile-skill/plan.md:13-19` are seven `- [x] A<n> ... (C<n>)` lines.
Verify: `[ "$(grep -cE '^- \[x\] A[0-9]+ .*\(C[0-9]+\)$' work/reconcile-skill/plan.md)" -eq 7 ] && ! grep -q '^- \[ \]' work/reconcile-skill/plan.md`
Verdict: SUPPORTED
Ran the two-part test -> exit 0; `work/reconcile-skill/plan.md:13-19` are seven `- [x] A<n> ... (C<n>)` lines, A1 through A7 naming C1 through C7, and no unticked box remains in the file; unticking A5 or stripping the `(C7)` tag from A7 each makes it exit 1.
