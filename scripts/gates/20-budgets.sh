#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Size budgets on source, docs and AGENTS.md."; exit 0; }

CODE_MAX=400
DOC_MAX=200
AGENTS_MAX=120
README_MAX=120

found=0
report() {
  found=1
  printf '%s: %s lines, budget %s\n' "$1" "$2" "$3"
}

budget_for() {
  case "$1" in
    AGENTS.md) echo "$AGENTS_MAX" ;;
    README.md) echo "$README_MAX" ;;
    *) echo "$DOC_MAX" ;;
  esac
}

while IFS= read -r f; do
  [ -f "$f" ] || continue
  el_is_generated "$f" && continue
  n="$(el_line_count "$f")"
  [ "$n" -gt "$CODE_MAX" ] && report "$f" "$n" "$CODE_MAX"
done < <(el_code_files | el_drop_linted)

while IFS= read -r f; do
  [ -f "$f" ] || continue
  max="$(budget_for "$f")"
  n="$(el_line_count "$f")"
  [ "$n" -gt "$max" ] && report "$f" "$n" "$max"
done < <(el_repo_files | grep -E '^(docs/|[A-Z]+\.md$)' | grep -vE '^(docs/decisions/|CHANGELOG\.md$)' || true)

[ "$found" -eq 0 ] && exit 0
echo
echo "Split it or cut it."
exit 1
