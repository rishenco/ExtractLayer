#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Each workspace runs its own lint, types and tests."; exit 0; }

manifests="$(el_workspaces)"
[ -z "$manifests" ] && { echo "no workspace yet — no lint, types or tests to run"; exit 0; }

ROOT="$PWD"
found=0

fail() { found=1; printf '%s\n' "$*"; }

run_in() {
  local dir="$1"; shift
  case "$dir" in
    /*) ( cd "$dir" && "$@" ) || return 1 ;;
    *) ( cd "$ROOT/$dir" && "$@" ) || return 1 ;;
  esac
}

need() {
  command -v "$1" >/dev/null 2>&1 && return 0
  fail "$2: $1 is not installed — its checks cannot run, so nothing here is verified"
  return 1
}

while IFS= read -r manifest; do
  dir="$(dirname "$manifest")"
  case "$(basename "$manifest")" in
    package.json)
      grep -qE '"check"[[:space:]]*:' "$manifest" \
        || { fail "$dir: package.json has no \"check\" script — put lint, typecheck and test behind it"; continue; }
      need npm "$dir" || continue
      [ -d "$dir/node_modules" ] || { fail "$dir: dependencies not installed — npm ci"; continue; }
      run_in "$dir" npm run --silent check || fail "$dir: npm run check failed"
      ;;
    go.mod)
      el_any_exists "$dir"/.golangci.{yml,yaml,toml,json} \
        || fail "$dir: no .golangci config — linting is unconfigured"
      [ -n "$(find "$dir" -name '*.go' -not -path '*/vendor/*' -print -quit)" ] || continue
      need go "$dir" || continue
      need golangci-lint "$dir" && { run_in "$dir" golangci-lint run ./... || fail "$dir: golangci-lint failed"; }
      run_in "$dir" go vet ./... || fail "$dir: go vet failed"
      run_in "$dir" go test ./... || fail "$dir: go test failed"
      ;;
    pyproject.toml)
      grep -q 'tool.ruff' "$manifest" || fail "$dir: no [tool.ruff] — linting is unconfigured"
      grep -q 'tool.mypy' "$manifest" || fail "$dir: no [tool.mypy] — type checking is unconfigured"
      [ -n "$(find "$dir" -name '*.py' -not -path '*/.venv/*' -print -quit)" ] || continue
      need ruff "$dir" && { run_in "$dir" ruff check . || fail "$dir: ruff failed"; }
      need mypy "$dir" && { run_in "$dir" mypy . || fail "$dir: mypy failed"; }
      need pytest "$dir" && { run_in "$dir" pytest -q || fail "$dir: pytest failed"; }
      ;;
  esac
done <<<"$manifests"

[ "$found" -eq 0 ] && exit 0
echo
echo "A workspace whose checks do not run has no definition of done."
exit 1
