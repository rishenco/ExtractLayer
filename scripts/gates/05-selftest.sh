#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/selftest.sh

[ "${1:-}" = "--describe" ] && { echo "Gates still fire on known violations, and only on those."; exit 0; }

fixture bad.ts '// explains the obvious
export const a = 1'
expect 10-comments.sh 1 "full-line comment is caught"

fixture trailing.ts 'export const retries = 3 // how many times we retry'
expect 10-comments.sh 1 "trailing comment is caught"

fixture jsx.tsx 'export const A = () => <div>{/* wraps the children */}</div>'
expect 10-comments.sh 1 "jsx comment is caught"

fixture q.sql '-- explains the obvious
select 1'
expect 10-comments.sh 1 "sql comment is caught"

fixture ok.ts 'export const url = "https://example.com"
// @ts-expect-error upstream types are wrong
export const n: number = "1" as never'
expect 10-comments.sh 0 "urls in strings and directives are allowed"

fixture mul.py 'total = (base
    * multiplier)'
expect 10-comments.sh 0 "arithmetic continuation is not a comment"

fixture priv.ts 'export class Counter {
  #count = 0
}'
expect 10-comments.sh 0 "private class fields are not comments"

fixture tags.go '//go:build linux
// +build linux

package main'
expect 10-comments.sh 0 "go build tags are directives"

fixture py_trailing.py 'total = 1  # explains the obvious'
expect 10-comments.sh 1 "trailing hash comment is caught"

fixture regex.ts 'export const parts = s.split(/\s*\/\/\s*/)'
expect 10-comments.sh 0 "a regex literal is not a comment"

fixture typed.ts 'export interface A { type: string } // why we do this'
expect 10-comments.sh 1 "a directive word elsewhere on the line does not exempt a comment"

add_file "café.ts" '// non-ascii paths are still scanned
export const a = 1'
printf '%s\n' "$WORK/café.ts" >"$WORK/list"
expect 10-comments.sh 1 "a non-ascii path is scanned when listed"

printf '%s' "$(for i in $(seq 401); do echo "export const v$i = $i"; done)" >"$WORK/nonl.ts"
printf '%s\n' "$WORK/nonl.ts" >"$WORK/list"
expect 20-budgets.sh 1 "oversized source without a trailing newline is caught"

fixture long.ts "$(for i in $(seq 401); do echo "export const v$i = $i"; done)"
expect 20-budgets.sh 1 "oversized source is caught"

fixture short.ts 'export const a = 1'
expect 20-budgets.sh 0 "source within budget passes"

fixture filler.ts 'export const s = "It is worth noting that this sentence is empty."'
expect 30-slop.sh 1 "filler phrasing is caught"

fixture curly.ts 'export const s = "It’s worth noting that this sentence is empty."'
expect 30-slop.sh 1 "filler with a typographic apostrophe is caught"

fixture filler.md 'It is worth noting that this sentence is empty.'
expect 30-slop.sh 1 "filler phrasing in markdown is caught"

fixture todo.md '- TODO: decide the retention window'
expect 30-slop.sh 1 "an unowned TODO in markdown is caught"

fixture clean.ts 'export const a = 1'
expect 30-slop.sh 0 "clean source passes"

fixture narrated.md 'The first slice ran on SQLite until a review round replaced it.'
expect 35-narration.sh 1 "session narration in committed markdown is caught"

fixture timeless.md 'Postgres is the only supported store.'
expect 35-narration.sh 0 "timeless markdown passes"

fixture work/nb/claims.md 'Restated after the second review round.'
expect 35-narration.sh 1 "a ledger under work/ has no memory of its review either"

fixture attributed.md 'Found in review: the owner asked for a gate instead of a test.'
expect 35-narration.sh 1 "a doc naming who asked for a change is caught"

fixture ownership.md 'The owner of a dataset decides who may read it.'
expect 35-narration.sh 0 "a doc about ownership is not attribution"

fixture docs/lessons.md '- Keep ledgers verdict-only — found when the founder caught a narrated preamble.'
expect 35-narration.sh 0 "lessons provenance may name who found it"

fixture doclink.md 'See docs/does-not-exist.md for details.'
expect 45-doc-links.sh 1 "a broken docs path in markdown is caught"

fixture untracked.md 'See scripts/gates/nothing-here.sh for details.'
expect 45-doc-links.sh 1 "a file git does not track yet is still scanned"

fixture wordlike.md 'The framework/plugin dir and the network/setup are fine.'
expect 45-doc-links.sh 0 "a word ending in a scanned directory name is not a path"

fixture resolves.md 'The gates live in scripts/gates/ and run from scripts/check.sh.'
expect 45-doc-links.sh 0 "a path that resolves passes"

fixture placeholder.md 'A plan lives at work/<slug>/plan.md.'
expect 45-doc-links.sh 0 "a placeholder segment is not a path to resolve"

fixture work/wl/notes.md 'See docs/does-not-exist.md.'
expect 45-doc-links.sh 0 "references inside work/ are not checked"


changed "ui/src/thing.ts"
EL_CHANGED_LIST="$WORK/changed" expect 40-changelog.sh 1 "source change without a changelog entry is caught"

changed "ui/src/thing.ts" "CHANGELOG.md"
EL_CHANGED_LIST="$WORK/changed" expect 40-changelog.sh 0 "source change with a changelog entry passes"

changed "docs/architecture.md"
EL_CHANGED_LIST="$WORK/changed" expect 40-changelog.sh 0 "docs-only change needs no changelog entry"

changed "ui/src/thing.ts"
EL_CHANGED_LIST="$WORK/changed" expect 70-approved-plan.sh 1 "source change with no approved plan is caught"

add_file work/wk/plan.md 'Status: Approved'
changed "ui/src/thing.ts" "$WORK/work/wk/plan.md"
EL_CHANGED_LIST="$WORK/changed" expect 70-approved-plan.sh 0 "source change with an approved plan passes"

add_file work/wk2/plan.md 'Status: Draft'
changed "ui/src/thing.ts" "$WORK/work/wk2/plan.md"
EL_CHANGED_LIST="$WORK/changed" expect 70-approved-plan.sh 1 "a draft plan does not count as approval"

add_file work/wk3/plan.md 'Status: Approved but not really'
changed "ui/src/thing.ts" "$WORK/work/wk3/plan.md"
EL_CHANGED_LIST="$WORK/changed" expect 70-approved-plan.sh 1 "a hedged status is not approval"

add_file stray/plan.md 'Status: Approved'
changed "ui/src/thing.ts" "$WORK/stray/plan.md"
EL_CHANGED_LIST="$WORK/changed" expect 70-approved-plan.sh 1 "a plan outside work/ is not approval"

printf '%s\n' "ui/src/thing.ts" >"$WORK/exempt"
changed "ui/src/thing.ts"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 70-approved-plan.sh 0 "a file exempted by trailer passes"

printf '%s\n' "ui/src/other.ts" >"$WORK/exempt"
changed "ui/src/thing.ts"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 70-approved-plan.sh 1 "an exemption for a different file does not carry over"

changed "docs/architecture.md"
EL_CHANGED_LIST="$WORK/changed" expect 70-approved-plan.sh 0 "docs-only change needs no plan"

printf '' >"$WORK/exempt"

changed "ui/src/thing.ts"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 1 "source change with no claims ledger is caught"

add_file work/cl/claims.md '## C1
Claim: make check passes.
Verify: make check
Verdict: SUPPORTED'
changed "ui/src/thing.ts" "$WORK/work/cl/claims.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 0 "a fully supported ledger passes"

add_file work/cl2/claims.md '## C1
Claim: make check passes.
Verify: make check
Verdict: FALSE'
changed "ui/src/thing.ts" "$WORK/work/cl2/claims.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 1 "a refuted claim blocks"

add_file work/cl3/claims.md '## C1
Claim: make check passes.
Verify: make check
Verdict: UNSUPPORTED'
changed "ui/src/thing.ts" "$WORK/work/cl3/claims.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 1 "a claim nobody could reproduce blocks"

add_file work/cl4/claims.md '## C1
Claim: make check passes.
Verify: make check
Verdict:

## C2
Claim: the parser handles empty input.
Verify: npm test -- parser
Verdict: SUPPORTED'
changed "ui/src/thing.ts" "$WORK/work/cl4/claims.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 1 "an unaudited claim blocks even when the others passed"

add_file work/cl5/claims.md '# Claims

Everything works.'
changed "ui/src/thing.ts" "$WORK/work/cl5/claims.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 1 "prose with no claim blocks"

add_file work/cl6/claims.md '## C1
Claim: make check passes.
Evidence: with this ledger unwritten, every other gate reported ok.
Verify: make check
Verdict: SUPPORTED'
changed "ui/src/thing.ts" "$WORK/work/cl6/claims.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 1 "evidence that describes the ledger rather than the tree blocks"

add_file work/cl7/claims.md '## C1
Claim: make check passes.
Evidence: make check prints all gates pass and exits 0.
Verify: make check
Verdict: SUPPORTED

Verified: I reran it and it passed.'
changed "ui/src/thing.ts" "$WORK/work/cl7/claims.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 1 "a line outside the claim blocks blocks"

add_file work/cl8/claims.md 'Six claims were re-audited after the review.

## C1
Claim: make check passes.
Evidence: make check prints all gates pass and exits 0.
Verify: make check
Verdict: SUPPORTED'
changed "ui/src/thing.ts" "$WORK/work/cl8/claims.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 1 "a preamble blocks"

add_file work/cl9/claims.md '## C1
Claim: make check passes.
Evidence: make check prints all gates pass and exits 0.
Verify: make check
Verdict: SUPPORTED'
changed "ui/src/thing.ts" "$WORK/work/cl9/claims.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 0 "a ledger of nothing but claim blocks and verdicts passes"

changed "docs/architecture.md"
EL_CHANGED_LIST="$WORK/changed" EL_EXEMPT_LIST="$WORK/exempt" \
  expect 75-claims.sh 0 "docs-only change needs no ledger"

mkdir -p "$WORK/hook/docs" "$WORK/hook/work/planned" "$WORK/hook/work/unplanned"
: >"$WORK/hook/docs/vision.md"
printf 'Status: Approved\n' >"$WORK/hook/work/planned/plan.md"
printf '## C1\n' >"$WORK/hook/work/unplanned/claims.md"
hook_out="$(CLAUDE_PROJECT_DIR="$WORK/hook" bash .claude/hooks/session-start.sh 2>/dev/null)"

grep -qx 'open work: planned (plan Approved)' <<<"$hook_out" || {
  found=1
  echo "session hook: does not report an approved plan"
}
grep -q 'unplanned' <<<"$hook_out" && {
  found=1
  echo "session hook: reports a slug with no plan as open work"
}
[ "$(grep -c '^open work:' <<<"$hook_out")" -eq 1 ] || {
  found=1
  echo "session hook: does not print exactly one state per slug"
}

: >"$WORK/empty"
if ! EL_FILE_LIST="$WORK/empty" bash -eo pipefail -c '. scripts/lib/files.sh; el_workspaces' >/dev/null 2>&1; then
  found=1
  echo "el_workspaces: exits non-zero under 'set -e -o pipefail' when no workspace exists"
fi

for sibling in scripts/gates/*-selftest*.sh; do
  [ -x "$sibling" ] && continue
  found=1
  echo "$sibling: not executable — the fixtures it carries never run"
done

[ "$found" -eq 0 ] && exit 0
echo
echo "A gate that stopped firing reports success it cannot back."
exit 1
