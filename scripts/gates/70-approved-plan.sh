#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Source changes trace to an approved plan."; exit 0; }

changed="$(el_changed_files)" || {
  echo "no base ref to compare against, so this gate can verify nothing"
  echo "  fetch the default branch; CI needs actions/checkout with fetch-depth: 0"
  exit 1
}
[ -z "$changed" ] && exit 0

relevant="$(printf '%s\n' "$changed" | el_filter_ext "$EL_CODE_EXT" | grep -vE "$EL_SKIP_DIRS" || true)"
[ -z "$relevant" ] && exit 0

unsummarized=""
while IFS= read -r f; do
  case "$f" in
    work/*/plan.md|*/work/*/plan.md)
      grep -qE '^Status:[[:space:]]*Approved[[:space:]]*$' "$f" 2>/dev/null || continue
      grep -qE '^## TL;DR[[:space:]]*$' "$f" 2>/dev/null && exit 0
      unsummarized="$f"
      ;;
  esac
done < <(printf '%s\n' "$changed")

blocked="$(printf '%s\n' "$relevant" | el_blocked_after_trailer)"

if [ -z "$blocked" ]; then
  echo "plan gate skipped by trailer for every changed source file"
  exit 0
fi

if [ -n "$unsummarized" ]; then
  echo "$unsummarized is approved but has no '## TL;DR' section."
  echo "The TL;DR is what the human approves from; add it and have the plan re-approved."
  exit 1
fi

echo "source changed with no approved plan in this branch:"
printf '%s\n' "$blocked" | sed 's/^/  /'
echo
echo "Run /plan, and have a human set 'Status: Approved' in work/<slug>/plan.md."
echo "To skip a file deliberately, the commit that touches it carries '$EL_TRAILER <reason>'."
exit 1
