#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Paths referenced from markdown outside work/ resolve, and none cites a line number."; exit 0; }

CITED_EXT='go|ts|tsx|js|jsx|mjs|cjs|py|rb|rs|java|kt|sql|sh|md|toml|json|yml|yaml'

refs() {
  grep -oE '(^|[^A-Za-z0-9_/])(docs|scripts|work)/[A-Za-z0-9._<>/-]*[A-Za-z0-9_>-]' "$1" \
    | sed -E 's|^[^A-Za-z]||' | sort -u
}

line_citations() {
  awk -v re="[A-Za-z0-9_./-]+\\.($CITED_EXT):[0-9]+" '
    /^[[:space:]]*```/ { fenced = !fenced; next }
    fenced { next }
    { rest = $0
      while (match(rest, re)) {
        printf "%d\t%s\n", NR, substr(rest, RSTART, RLENGTH)
        rest = substr(rest, RSTART + RLENGTH)
      } }
  ' "$1"
}

found=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  el_is_generated "$f" && continue
  while IFS= read -r ref; do
    case "$ref" in *'<'*) continue ;; esac
    [ -e "$ref" ] && continue
    found=1
    printf '%s: broken reference %s\n' "$f" "$ref"
  done < <(refs "$f")
  while IFS=$'\t' read -r n cite; do
    [ -n "$n" ] || continue
    found=1
    printf '%s:%s: cites a line, %s\n' "$f" "$n" "$cite"
  done < <(line_citations "$f")
done < <(el_repo_files | grep -E '\.md$' | grep -vE '(^|/)work/' | sort -u)

[ "$found" -eq 0 ] && exit 0
echo
echo "Fix the path or the reference; a doc pointing nowhere misleads the next reader."
echo "Name the rule, the symbol or the section — a line number is right until the next edit to that file."
exit 1
