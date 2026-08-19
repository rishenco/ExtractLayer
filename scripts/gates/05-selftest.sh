#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

[ "${1:-}" = "--describe" ] && { echo "Gates still fire on known violations, and only on those."; exit 0; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

found=0

add_file() {
  mkdir -p "$(dirname "$WORK/$1")"
  printf '%s\n' "$2" >"$WORK/$1"
}

fixture() {
  add_file "$1" "$2"
  printf '%s\n' "$WORK/$1" >"$WORK/list"
}

changed() { printf '%s\n' "$@" >"$WORK/changed"; }

expect() {
  local gate="$1" want="$2" name="$3" got
  EL_FILE_LIST="$WORK/list" "./scripts/gates/$gate" >/dev/null 2>&1
  got=$?
  [ "$got" -eq "$want" ] && return 0
  found=1
  printf '%s: %s exited %s, expected %s\n' "$name" "$gate" "$got" "$want"
}

expect_silent_about() {
  local gate="$1" pattern="$2" name="$3" out
  out="$(EL_FILE_LIST="$WORK/list" "./scripts/gates/$gate" 2>&1)"
  grep -qE "$pattern" <<<"$out" || return 0
  found=1
  printf '%s: %s still reports %s\n' "$name" "$gate" "$pattern"
}

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

fixture ws1/package.json '{"name":"fixture","scripts":{}}'
expect 50-architecture.sh 1 "workspace without boundary config is caught"
expect 60-workspaces.sh 1 "workspace without a check script is caught"

add_file ws2/.dependency-cruiser.js 'module.exports = { forbidden: [] }'
fixture ws2/package.json '{"name":"fixture","scripts":{"check":"true"}}'
expect 50-architecture.sh 0 "node workspace with a boundary config passes"

add_file gows/.go-arch-lint.yml 'version: 3'
fixture gows/go.mod 'module fixture'
expect 50-architecture.sh 0 "go workspace with a boundary config passes"

add_file pyws/pyproject.toml '[tool.importlinter]
root_package = "fixture"
[tool.ruff]
[tool.mypy]'
fixture pyws/pyproject.toml "$(cat "$WORK/pyws/pyproject.toml")"
expect 50-architecture.sh 0 "python workspace with importlinter contracts passes"
expect 60-workspaces.sh 0 "python workspace with no sources and configured tooling passes"

add_file gows2/.golangci.yml 'linters:
  enable: [govet]'
fixture gows2/go.mod 'module fixture'
expect_silent_about 60-workspaces.sh 'no .golangci config' "a present golangci config is detected"

fixture lint1/package.json '{"name":"fixture","scripts":{"check":"true"}}'
expect 55-lint-config.sh 1 "a workspace without a linter config is caught"

add_file lint2/eslint.config.js 'export default []'
add_file lint2/bad.ts '// explains the obvious
export const a = 1'
printf '%s\n%s\n' "$WORK/lint2/package.json" "$WORK/lint2/bad.ts" >"$WORK/list"
add_file lint2/package.json '{"name":"fixture","scripts":{"check":"true"}}'
expect 10-comments.sh 0 "a linted workspace is no longer scanned by the floor"

printf '%s\n' "$WORK/lint2/bad.ts" >"$WORK/list"
expect 10-comments.sh 1 "the floor still scans a file outside any linted workspace"

add_file bad.sh '# explains the loop
echo hi'
add_file pyproject.toml '[tool.ruff]
line-length = 99'
printf '%s\n%s\n' "$WORK/pyproject.toml" "$WORK/bad.sh" >"$WORK/list"
expect 10-comments.sh 1 "a root workspace does not retire the floor for what its linter cannot parse"

if command -v npm >/dev/null 2>&1; then
  mkdir -p "$WORK/ws2/node_modules"
  fixture ws2/package.json '{"name":"fixture","version":"1.0.0","scripts":{"check":"true"}}'
  expect 60-workspaces.sh 0 "node workspace with a passing check script passes"
else
  echo "npm not installed — skipped the 60-workspaces pass case"
fi

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

[ "$found" -eq 0 ] && exit 0
echo
echo "A gate that stopped firing reports success it cannot back."
exit 1
