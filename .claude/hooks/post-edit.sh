#!/usr/bin/env bash
set -uo pipefail

input="$(cat 2>/dev/null || true)"
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

edited="$(grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' <<<"$input" \
  | head -n 1 \
  | sed 's/.*:[[:space:]]*"\(.*\)"$/\1/')"

list="$(mktemp)"
trap 'rm -f "$list"' EXIT

if [ -n "$edited" ] && [ -f "$edited" ]; then
  printf '%s\n' "$edited" >"$list"
else
  {
    git diff --name-only HEAD
    git ls-files --others --exclude-standard
  } 2>/dev/null | sort -u >"$list"
fi
[ -s "$list" ] || exit 0

report=""
for gate in 10-comments 30-slop; do
  out="$(EL_FILE_LIST="$list" "./scripts/gates/$gate.sh" 2>&1)" || report+="$out"$'\n'
done

[ -z "$report" ] && exit 0
printf '%s' "$report" >&2
exit 2
