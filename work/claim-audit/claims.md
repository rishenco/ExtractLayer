# Claims — claim-audit

Written after the code was committed, because `el_trailer_exempt` never exempts a file with
uncommitted changes and a ledger written on a dirty tree claims a state no gate can reach.

## C1
Claim: `make check` exits 0 on this branch as committed.
Evidence: every gate reports ok.
Verify: make check; echo "exit=$?"
Verdict:

## C2
Claim: `75-claims.sh` blocks a source change that ships no claims ledger.
Evidence: the gate exits 1 and names the unledgered files.
Verify: T=$(mktemp -d); printf 'ui/src/a.ts\n' >"$T/c"; printf '' >"$T/e"; EL_CHANGED_LIST="$T/c" EL_EXEMPT_LIST="$T/e" ./scripts/gates/75-claims.sh; echo "exit=$?"
Verdict:

## C3
Claim: `75-claims.sh` blocks a ledger whose claim carries a `FALSE` verdict, and passes the
same ledger when the verdict is `SUPPORTED`.
Evidence: exit 1 for FALSE, exit 0 for SUPPORTED, identical input otherwise.
Verify: T=$(mktemp -d); mkdir -p "$T/work/x"; printf 'ui/src/a.ts\n%s\n' "$T/work/x/claims.md" >"$T/c"; printf '' >"$T/e"; for v in FALSE SUPPORTED; do printf '## C1\nClaim: x\nVerify: true\nVerdict: %s\n' "$v" >"$T/work/x/claims.md"; EL_CHANGED_LIST="$T/c" EL_EXEMPT_LIST="$T/e" ./scripts/gates/75-claims.sh >/dev/null 2>&1; echo "$v exit=$?"; done
Verdict:

## C4
Claim: `05-selftest.sh` fails if `75-claims.sh` stops rejecting `FALSE` and `UNSUPPORTED`
verdicts, so the gate cannot silently stop working.
Evidence: the selftest names the refuted-claim and unreproducible-claim cases as exiting 0
when 1 was expected.
Verify: D=$(mktemp -d); cp -r . "$D/r" >/dev/null 2>&1; cd "$D/r" && sed -i 's/^  \[ -n "\$bad" \]/  false/' scripts/gates/75-claims.sh && ./scripts/gates/05-selftest.sh; echo "exit=$?"
Verdict:

## C5
Claim: `70-approved-plan.sh` and `75-claims.sh` both obtain their trailer exemption from
`el_blocked_after_trailer`, so there is one escape hatch rather than two.
Evidence: both gates call that function and neither defines its own trailer handling.
Verify: grep -n 'el_blocked_after_trailer\|Skips-plan-gate\|EL_TRAILER' scripts/gates/70-approved-plan.sh scripts/gates/75-claims.sh scripts/lib/files.sh
Verdict:

## C6
Claim: `adversarial-reviewer.md` no longer instructs the reviewer to run `make check`, and no
longer asks whether tests fail when behaviour regresses.
Evidence: neither instruction appears in the file, and the file directs both to the auditor.
Verify: grep -n 'make check\|fails when the behaviour regresses' .claude/agents/adversarial-reviewer.md; echo "grep exit=$?"
Verdict:

## C7
Claim: the `claim-auditor` subagent is wired into the loop, not merely present as a file: the
`/build` skill, `CLAUDE.md` and `AGENTS.md` each direct work to it.
Evidence: each of those three files names it.
Verify: grep -rn 'claim-auditor' .claude/skills/build/SKILL.md CLAUDE.md AGENTS.md
Verdict:

## C8
Claim: nothing in the committed change alters behaviour outside the claim-audit mechanism and
its wiring — the diff touches gates, agents, skills and docs, and no product code.
Evidence: the committed diff contains no files outside `scripts/`, `.claude/`, `docs/`,
`.github/`, `AGENTS.md`, `CLAUDE.md` and `CHANGELOG.md`.
Verify: git diff --name-only HEAD~1..HEAD
Verdict:
