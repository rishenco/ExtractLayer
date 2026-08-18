#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Every docs/, scripts/ or work/ path referenced from markdown outside work/ resolves."; exit 0; }

refs() {
  grep -oE '(^|[^A-Za-z0-9_/])(docs|scripts|work)/[A-Za-z0-9._<>/-]*[A-Za-z0-9_>-]' "$1" \
    | sed -E 's|^[^A-Za-z]||' | sort -u
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
done < <(el_repo_files | grep -E '\.md$' | grep -vE '(^|/)work/' | sort -u)

[ "$found" -eq 0 ] && exit 0
echo
echo "Fix the path or the reference; a doc pointing nowhere misleads the next reader."
exit 1
