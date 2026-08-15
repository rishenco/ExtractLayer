# Claims — claim-audit

Written after the code was committed, because `el_trailer_exempt` never exempts a file with
uncommitted changes and a ledger written on a dirty tree claims a state no gate can reach.

## C1
Claim: `make check` exits 0 on this branch as committed.
Evidence: every gate reports ok.
Verify: make check; echo "exit=$?"
Verdict: SUPPORTED
Checked: ran `make check; echo "exit=$?"` -> every gate prints ok, `all gates pass`, exit=0; unchanged across working-tree states (untracked ledger present, ledger deleted in a copy, and now committed as 0380ff7 with a clean tree), and `bash -x scripts/gates/75-claims.sh` shows the gate exiting 0 at the empty-`blocked` test without reading any ledger.

## C2
Claim: `75-claims.sh` blocks a source change that ships no claims ledger.
Evidence: the gate exits 1 and names the unledgered files.
Verify: T=$(mktemp -d); printf 'ui/src/a.ts\n' >"$T/c"; printf '' >"$T/e"; EL_CHANGED_LIST="$T/c" EL_EXEMPT_LIST="$T/e" ./scripts/gates/75-claims.sh; echo "exit=$?"
Verdict: SUPPORTED
Checked: ran the command -> exit=1, printing "source changed with no claims ledger:" then "  ui/src/a.ts" and the instruction to write work/<slug>/claims.md.

## C3
Claim: `75-claims.sh` blocks a ledger whose claim carries a `FALSE` verdict, and passes the
same ledger when the verdict is `SUPPORTED`.
Evidence: exit 1 for FALSE, exit 0 for SUPPORTED, identical input otherwise.
Verify: T=$(mktemp -d); mkdir -p "$T/work/x"; printf 'ui/src/a.ts\n%s\n' "$T/work/x/claims.md" >"$T/c"; printf '' >"$T/e"; for v in FALSE SUPPORTED; do printf '## C1\nClaim: x\nVerify: true\nVerdict: %s\n' "$v" >"$T/work/x/claims.md"; EL_CHANGED_LIST="$T/c" EL_EXEMPT_LIST="$T/e" ./scripts/gates/75-claims.sh >/dev/null 2>&1; echo "$v exit=$?"; done
Verdict: SUPPORTED
Checked: ran the command -> `FALSE exit=1`, `SUPPORTED exit=0`; re-run with output shown, the FALSE case prints "unresolved 4:Verdict: FALSE" from the same ledger path, so the verdict is what drives it.

## C4
Claim: `05-selftest.sh` fails if `75-claims.sh` stops rejecting `FALSE` and `UNSUPPORTED`
verdicts, so the gate cannot silently stop working.
Evidence: the selftest names the refuted-claim and unreproducible-claim cases as exiting 0
when 1 was expected.
Verify: D=$(mktemp -d); cp -r . "$D/r" >/dev/null 2>&1; cd "$D/r" && sed -i 's/^  \[ -n "\$bad" \]/  false/' scripts/gates/75-claims.sh && ./scripts/gates/05-selftest.sh; echo "exit=$?"
Verdict: SUPPORTED
Checked: ran the command -> exit=1 with exactly "a refuted claim blocks: 75-claims.sh exited 0, expected 1" and "a claim nobody could reproduce blocks: 75-claims.sh exited 0, expected 1".

## C5
Claim: `70-approved-plan.sh` and `75-claims.sh` both obtain their trailer exemption from
`el_blocked_after_trailer`, so there is one escape hatch rather than two.
Evidence: both gates call that function and neither defines its own trailer handling.
Verify: grep -n 'el_blocked_after_trailer\|Skips-plan-gate\|EL_TRAILER' scripts/gates/70-approved-plan.sh scripts/gates/75-claims.sh scripts/lib/files.sh
Verdict: SUPPORTED
Checked: ran the grep -> `el_blocked_after_trailer` called at 70-approved-plan.sh:26 and 75-claims.sh:18, trailer parsing only at scripts/lib/files.sh:57,75; grep alone cannot settle the negative, so I read both gates end to end: neither inspects a commit message, 70's other `EL_TRAILER` use is an echo string, and neutering `el_blocked_after_trailer` in a copy makes both gates exit 1 despite an exempt list.

## C6
Claim: `adversarial-reviewer.md` no longer instructs the reviewer to run `make check`, and no
longer asks whether tests fail when behaviour regresses.
Evidence: neither instruction appears in the file, and the file directs both to the auditor.
Verify: grep -n 'make check\|fails when the behaviour regresses' .claude/agents/adversarial-reviewer.md; echo "grep exit=$?"
Verdict: SUPPORTED
Checked: ran the grep -> one hit, line 13, and grep exit=0, so the grep does not settle the claim; opened the file: line 13 reads "Do not run `make check` and do not test anything", the Correctness section ends at question 13, and the 0ab6ca7 diff shows the old "Run `make check` yourself" line and question 14 "fails when the behaviour regresses" both removed, with lines 13-15 and 20-21 sending both to `claim-auditor`.

## C7
Claim: the `claim-auditor` subagent is wired into the loop, not merely present as a file: the
`/build` skill, `CLAUDE.md` and `AGENTS.md` each direct work to it.
Evidence: each of those three files names it.
Verify: grep -rn 'claim-auditor' .claude/skills/build/SKILL.md CLAUDE.md AGENTS.md
Verdict: SUPPORTED
Checked: ran the grep -> SKILL.md:50 "Run the `claim-auditor` subagent", CLAUDE.md:8 "After any change, run the `claim-auditor` subagent on what you assert", AGENTS.md:25 inside the loop paragraph whose sequence at line 21 is "`/build` -> claim audit -> code review -> PR"; opened all three, each directs work to it rather than merely naming a file.

## C8
Claim: commit `0ab6ca7` touches no path outside `scripts/`, `.claude/`, `docs/`, `.github/`,
`AGENTS.md`, `CLAUDE.md` and `CHANGELOG.md`.
Evidence: listing its paths and removing that set leaves nothing.
Verify: git diff --name-only 0ab6ca7~1..0ab6ca7 | grep -cvE '^(scripts/|\.claude/|docs/|\.github/|AGENTS\.md|CLAUDE\.md|CHANGELOG\.md)'
Verdict:

## C9
Claim: the repository contains no product source — every file `el_code_files` reports is a gate,
a library for gates, or a hook.
Evidence: the listing contains only paths under `scripts/` and `.claude/`.
Verify: bash -c '. scripts/lib/files.sh; el_code_files' | grep -cvE '^(scripts/|\.claude/)'
Verdict:

## C10
Claim: `/build` still requires the CHANGELOG entry that the `## Verify` section used to carry,
after that section was replaced by Claim and Audit.
Evidence: the skill names `CHANGELOG.md` and `## [Unreleased]`.
Verify: grep -n 'CHANGELOG.md\|Unreleased\|acceptance criterion' .claude/skills/build/SKILL.md
Verdict:
