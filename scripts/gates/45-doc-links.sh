#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

[ "${1:-}" = "--describe" ] && { echo "Every docs/, scripts/ or work/ path referenced from markdown outside work/ resolves."; exit 0; }

found=0
while IFS= read -r f; do
  while IFS= read -r ref; do
    case "$ref" in *'<'*) continue ;; esac
    ref="${ref%.}"
    [ -e "$ref" ] && continue
    found=1
    printf '%s: broken reference %s\n' "$f" "$ref"
  done < <(grep -oE '(docs|scripts|work)/[A-Za-z0-9._<>/-]*[A-Za-z0-9_>-]' "$f" | sort -u)
done < <(git ls-files '*.md' | grep -v '^work/')

[ "$found" -eq 0 ] && exit 0
echo
echo "Fix the path or the reference; a doc pointing nowhere misleads the next reader."
exit 1
