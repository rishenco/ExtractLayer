#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Committed docs carry no session narration."; exit 0; }

PHRASES=(
  "the founder"
  "the (owner|reviewer) (asked|wanted|requested|said)"
  "first[- ]slice"
  "this (session|conversation)"
  "our (chat|conversation)"
  "review round"
  "was removed by"
  "previous implementation"
  "design session"
)
RELIC="$(IFS='|'; echo "${PHRASES[*]}")"

targets() {
  el_repo_files | grep -E '\.md$' \
    | grep -vE '(^|/)docs/lessons\.md$' \
    | sort -u
}

found=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  el_is_generated "$f" && continue
  hits="$(grep -niE "$RELIC" "$f" || true)"
  if [ -n "$hits" ]; then
    found=1
    printf '%s\n' "$hits" | sed "s|^|relic   $f:|"
  fi
done < <(targets)

[ "$found" -eq 0 ] && exit 0
echo
echo "A committed doc has one role and no memory of the conversation that produced it."
echo "State what is true now; the trail lives in git history and docs/lessons.md."
exit 1
