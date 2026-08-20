#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "No code comments outside directives."; exit 0; }

DIRECTIVE='nolint|go:|\+build|eslint|@ts-|biome-|prettier-|oxlint|deno-|noqa|type:|ruff:|pylint:|mypy:|fmt:|coverage:|istanbul|shellcheck|sourceMappingURL|DO NOT EDIT'
ALLOW="(//|/\*|#|--)[[:space:]]*($DIRECTIVE)"

strip_strings() {
  sed -E 's/"([^"\\]|\\.)*"//g' \
    | sed -E "s/'([^'\\\\]|\\\\.)*'//g" \
    | sed -E 's/`([^`\\]|\\.)*`//g'
}

marker_for() {
  case "${1##*.}" in
    go|ts|tsx|js|jsx|mjs|cjs|java|kt|rs) echo '(//|/\*)' ;;
    py|rb|sh) echo '(^[[:space:]]*#[^!]|[^$({[:alnum:]]#[[:space:]]|[[:space:]]#[^{])' ;;
    sql) echo '(--|/\*)' ;;
    *) echo '' ;;
  esac
}

found=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  el_is_generated "$f" && continue
  marker="$(marker_for "$f")"
  [ -z "$marker" ] && continue
  hits="$(strip_strings <"$f" | grep -nE "$marker" | grep -vE "$ALLOW" || true)"
  [ -z "$hits" ] && continue
  found=1
  printf '%s\n' "$hits" | sed "s|^|$f:|"
done < <(el_code_files | grep -vE '(^|/)scripts/gates/05-selftest\.sh$' | el_drop_linted || true)

[ "$found" -eq 0 ] && exit 0
echo
echo "Delete them, or make the code say it. Directives and unreadable algorithms are the exceptions."
echo "Comprehensive comment linting belongs to each workspace linter; this gate is the floor, not the ceiling."
exit 1
