## C1
Claim: `.claude/skills/reconcile/SKILL.md` exists and its frontmatter description says when to run the skill.
Evidence: `.claude/skills/reconcile/SKILL.md:3` reads "Use when the written record has drifted from the code, or before planning from a document nobody has checked lately."
Verify: `[ -f .claude/skills/reconcile/SKILL.md ] && sed -n '1,5p' .claude/skills/reconcile/SKILL.md | grep -q '^description: .*Use when'`
Verdict:

## C2
Claim: The skill's first two bash blocks, run verbatim against this tree, print three lines whose tokens are exactly `add_pairs`, `assign_split` and `derived_values`.
Evidence: the two blocks at `.claude/skills/reconcile/SKILL.md:11-14` and `:20-31` print `docs/lessons.md:14: assign_split`, `docs/lessons.md:20: add_pairs` and `docs/lessons.md:20: derived_values`, and nothing else.
Verify: `[ "$(awk '/^```bash$/{n++;f=1;next} /^```$/{f=0} f && n<=2' .claude/skills/reconcile/SKILL.md | bash | awk '{print $NF}' | sort | tr '\n' ' ')" = "add_pairs assign_split derived_values " ]`
Verdict:

## C3
Claim: The skill states a five-entry precedence ladder for the canonical home of a duplicated rule, and states that every losing copy becomes a pointer to the winner rather than being deleted.
Evidence: `.claude/skills/reconcile/SKILL.md:61` introduces the ladder, `:63-67` are its five entries, and `:69` reads "Every losing copy becomes a pointer to the winner."
Verify: `grep -q 'The canonical home is the first of these that can hold the rule' .claude/skills/reconcile/SKILL.md && [ "$(grep -cE '^[1-5]\. ' .claude/skills/reconcile/SKILL.md)" -eq 5 ] && grep -q 'becomes a pointer to the winner' .claude/skills/reconcile/SKILL.md`
Verdict:

## C4
Claim: The skill carries a "Do not flag" section of five entries and states that nothing under `work/` is edited.
Evidence: `.claude/skills/reconcile/SKILL.md:71-77` is the section with five bullets; `:81` reads "Nothing under `work/`."
Verify: `grep -q '^## Do not flag' .claude/skills/reconcile/SKILL.md && [ "$(awk '/^## Do not flag/{f=1;next} /^## /{f=0} f && /^- /' .claude/skills/reconcile/SKILL.md | wc -l)" -eq 5 ] && grep -q '^Nothing under `work/`' .claude/skills/reconcile/SKILL.md`
Verdict:

## C5
Claim: The skill states that its citation scan reads identifiers only and that a citation carrying no identifier is invisible to it.
Evidence: `.claude/skills/reconcile/SKILL.md:35` reads "The scan reads identifiers only. A citation carrying no identifier — a component named in words alone — is invisible to it and rots the same way."
Verify: `grep -q 'The scan reads identifiers only' .claude/skills/reconcile/SKILL.md && grep -q 'A citation carrying no identifier' .claude/skills/reconcile/SKILL.md`
Verdict:

## C6
Claim: `/reconcile` is named in `CLAUDE.md` and in `README.md`.
Evidence: `CLAUDE.md:6` and `README.md:13`.
Verify: `grep -q '/reconcile' CLAUDE.md && grep -q '/reconcile' README.md`
Verdict:

## C7
Claim: `make check` passes on this tree.
Evidence: it prints `all gates pass` across all 12 gates, `05-selftest` through `75-claims`.
Verify: `make check`
Verdict:
