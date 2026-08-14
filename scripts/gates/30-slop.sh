#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "No filler phrasing or unowned TODOs."; exit 0; }

Q="('|’)?"
PHRASES=(
  "it${Q}s (important|worth) (to note|noting)"
  "it is (important|worth) (to note|noting)"
  "keep in mind that"
  "in conclusion"
  "as an AI"
  "let${Q}s dive in"
  "delve (in)?to"
  "seamlessly integrate"
  "leverage the power of"
  "comprehensive solution"
  "in today${Q}s fast-paced"
  "simply put"
  "lorem ipsum"
  "I hope this helps"
)
FILLER="$(IFS='|'; echo "${PHRASES[*]}")"

targets() {
  { el_code_files; el_repo_files | grep -E '\.md$' || true; } \
    | grep -vE '^(scripts/gates/|work/)' | sort -u
}

found=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  el_is_generated "$f" && continue

  hits="$(grep -niE "$FILLER" "$f" || true)"
  if [ -n "$hits" ]; then
    found=1
    printf '%s\n' "$hits" | sed "s|^|filler  $f:|"
  fi

  todos="$(grep -nE '(^|[^"'"'"'[:alnum:]])(TODO|FIXME|XXX|HACK)([[:space:]:(]|$)' "$f" \
    | grep -vE '#[0-9]{1,6}([^0-9a-fA-F]|$)|https?://' || true)"
  if [ -n "$todos" ]; then
    found=1
    printf '%s\n' "$todos" | sed "s|^|unowned $f:|"
  fi
done < <(targets)

[ "$found" -eq 0 ] && exit 0
echo
echo "Cut the sentence. A TODO without an issue number or link is a note to nobody."
exit 1
