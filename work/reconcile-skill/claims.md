## C1
Claim: `.claude/skills/reconcile/SKILL.md` exists and its frontmatter description says when to run the skill.
Evidence: `.claude/skills/reconcile/SKILL.md:3` reads "Use when the written record has drifted from the code, or before planning from a document nobody has checked lately."
Verify: `[ -f .claude/skills/reconcile/SKILL.md ] && sed -n '1,5p' .claude/skills/reconcile/SKILL.md | grep -q '^description: .*Use when'`
Verdict: SUPPORTED
Ran the two-part test -> exit 0; line 3 is the description and reads "Use when the written record has drifted from the code, or before planning from a document nobody has checked lately." verbatim; rewriting `Use when` as `It runs when` in a copy makes the same grep exit 1.

## C2
Claim: The skill's first two bash blocks, run verbatim against this tree, print three lines whose tokens are exactly `add_pairs`, `assign_split` and `derived_values`.
Evidence: the two blocks at `.claude/skills/reconcile/SKILL.md:12-16` and `:24-35` print `docs/lessons.md:14: assign_split`, `docs/lessons.md:20: add_pairs` and `docs/lessons.md:20: derived_values`, and nothing else.
Verify: `[ "$(awk '/^```bash$/{n++;f=1;next} /^```$/{f=0} f && n<=2' .claude/skills/reconcile/SKILL.md | bash | awk '{print $NF}' | sort | tr '\n' ' ')" = "add_pairs assign_split derived_values " ]`
Verdict: SUPPORTED
Ran the extraction into `bash` -> exit 0; the blocks at `:12-16` and `:24-35` print `docs/lessons.md:14: assign_split`, `docs/lessons.md:20: add_pairs`, `docs/lessons.md:20: derived_values` and nothing else; a fourth dangling token planted in a new `docs/` file appears in the output and makes the command exit 1.

## C3
Claim: The skill states a five-entry precedence ladder for the canonical home of a duplicated rule, and states that every losing copy becomes a pointer to the winner rather than being deleted.
Evidence: `.claude/skills/reconcile/SKILL.md:68` introduces the ladder, `:70-74` are its five entries, and `:76` reads "Every losing copy becomes a pointer to the winner."
Verify: `grep -q 'The canonical home is the first of these that can hold the rule' .claude/skills/reconcile/SKILL.md && [ "$(grep -cE '^[1-5]\. ' .claude/skills/reconcile/SKILL.md)" -eq 5 ] && grep -q 'becomes a pointer to the winner' .claude/skills/reconcile/SKILL.md`
Verdict: SUPPORTED
Ran the three-part grep -> exit 0: the ladder opener at `:68`, five entries matching `^[1-5]. ` at `:70-74`, and `:76` reading "Every losing copy becomes a pointer to the winner."; dropping entry 5 in a copy gives a count of 4, and rewording either sentence makes its grep exit 1.

## C4
Claim: The skill carries a "Do not flag" section of five entries and states that nothing under `work/` is edited.
Evidence: `.claude/skills/reconcile/SKILL.md:78-84` is the section with five bullets; `:88` reads "Nothing under `work/`."
Verify: `grep -q '^## Do not flag' .claude/skills/reconcile/SKILL.md && [ "$(awk '/^## Do not flag/{f=1;next} /^## /{f=0} f && /^- /' .claude/skills/reconcile/SKILL.md | wc -l)" -eq 5 ] && grep -q '^Nothing under `work/`' .claude/skills/reconcile/SKILL.md`
Verdict: SUPPORTED
Ran the three-part test -> exit 0: heading at `:78`, five bullets at `:80-84`, and `:88` opening "Nothing under" the `work/` path; deleting one bullet in a copy gives a count of 4 and rewording line 88 makes its grep exit 1.

## C5
Claim: The skill states that its citation scan reads identifiers only and that a citation carrying no identifier is invisible to it.
Evidence: `.claude/skills/reconcile/SKILL.md:39` reads "Blind spot: the scan reads identifiers only. A citation carrying no identifier — a component named in words alone — is invisible to it and rots the same way."
Verify: `grep -q '^Blind spot: the scan reads identifiers only' .claude/skills/reconcile/SKILL.md && grep -q 'A citation carrying no identifier' .claude/skills/reconcile/SKILL.md`
Verdict: SUPPORTED
Ran both greps -> exit 0, both matching line 39, which opens "Blind spot: the scan reads identifiers only. A citation carrying no identifier — a component named in words alone — is invisible to it and rots the same way."; rewording either clause in a copy makes its grep exit 1.

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
Ran `make check` -> every gate `ok` from `05-selftest` to `75-claims`, twelve of them, then `all gates pass`, exit 0, with the eleven verdicts written; on the same tree with the last two verdict lines blank `75-claims` exits 1 on `11 claims but 9 verdicts`.

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

## C10
Claim: The contradictions block prints exactly one line against this tree, and printing a planted line whose magnitude is backticked takes it to two.
Evidence: it prints `AGENTS.md:67`, whose `120` matches `AGENTS_MAX=120` at `scripts/gates/20-budgets.sh:10`; a planted `docs/` line reading "`scripts/gates/20-budgets.sh` caps `AGENTS.md` at `999` lines" is printed as a second line.
Verify: `b() { awk '/^```bash$/{n++;f=1;next} /^```$/{f=0} f && (n==1 || n==3)' .claude/skills/reconcile/SKILL.md; }; [ "$(b | bash | grep -c .)" -eq 1 ] && printf -- '- `scripts/gates/20-budgets.sh` caps `AGENTS.md` at `999` lines.\n' > docs/_c10probe.md && o="$(b | bash)"; rm -f docs/_c10probe.md; [ "$(printf '%s\n' "$o" | grep -c .)" -eq 2 ] && printf '%s\n' "$o" | grep -q _c10probe`
Verdict: SUPPORTED
Ran the compound test -> exit 0; blocks 1 and 3 print one line, `AGENTS.md:67`, whose `120` matches `AGENTS_MAX=120` at `scripts/gates/20-budgets.sh:10`, and the planted `999` line is printed second and named in the output; the same blocks with the backtick-unwrapping `sed` removed print only `AGENTS.md:67` while the probe is in place, so the unwrap is what catches it.

## C11
Claim: Both shared file lists derive from `el_repo_files` in `scripts/lib/files.sh` rather than calling `git ls-files` directly, and `prose` covers every markdown file outside `work/`, `.claude/skills/build/SKILL.md` included.
Evidence: `.claude/skills/reconcile/SKILL.md:13-15`; the list is 28 files and contains `.claude/skills/build/SKILL.md`.
Verify: `grep -q '^\. scripts/lib/files\.sh$' .claude/skills/reconcile/SKILL.md && ! grep -q 'git ls-files' .claude/skills/reconcile/SKILL.md && . scripts/lib/files.sh && el_repo_files | grep -E '\.md$' | grep -vE '(^|/)work/' | grep -qx '.claude/skills/build/SKILL.md'`
Verdict: SUPPORTED
Ran the four-part test -> exit 0; `:13-15` are the `. scripts/lib/files.sh` line and the two definitions, no `git ls-files` appears anywhere in the file, and the list is 28 markdown files including `.claude/skills/build/SKILL.md`; rewording the source line, reintroducing `git ls-files`, or filtering the list by `EL_SKIP_DIRS` each make it exit 1, the last dropping that file and all of `docs/`, 16 of the 28.
