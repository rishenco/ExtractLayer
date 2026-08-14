#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Source changes trace to an approved plan."; exit 0; }

TRAILER='Skips-plan-gate:'

changed="$(el_changed_files)" || {
  echo "no base ref to compare against, so this gate can verify nothing"
  echo "  fetch the default branch; CI needs actions/checkout with fetch-depth: 0"
  exit 1
}
[ -z "$changed" ] && exit 0

relevant="$(printf '%s\n' "$changed" | el_filter_ext "$EL_CODE_EXT" | grep -vE "$EL_SKIP_DIRS" || true)"
[ -z "$relevant" ] && exit 0

while IFS= read -r f; do
  case "$f" in
    work/*/plan.md|*/work/*/plan.md)
      grep -qE '^Status:[[:space:]]*Approved[[:space:]]*$' "$f" 2>/dev/null && exit 0
      ;;
  esac
done < <(printf '%s\n' "$changed")

exempt_files() {
  if [ -n "${EL_EXEMPT_LIST:-}" ]; then
    cat "$EL_EXEMPT_LIST"
    return 0
  fi
  local base dirty f c commits ok
  base="$(el_base_ref)" || return 0
  dirty="$( { git diff --name-only HEAD; git ls-files --others --exclude-standard; } 2>/dev/null )"
  while IFS= read -r f; do
    printf '%s\n' "$dirty" | grep -qxF "$f" && continue
    commits="$(git log --format='%H' "$base"..HEAD -- "$f" 2>/dev/null)"
    [ -z "$commits" ] && continue
    ok=1
    while IFS= read -r c; do
      git log -1 --format='%B' "$c" | grep -qE "^$TRAILER[[:space:]]*\S" || { ok=0; break; }
    done <<<"$commits"
    [ "$ok" -eq 1 ] && printf '%s\n' "$f"
  done <<<"$relevant"
}

exempt="$(exempt_files)"
blocked=""
while IFS= read -r f; do
  printf '%s\n' "$exempt" | grep -qxF "$f" && continue
  blocked+="$f"$'\n'
done <<<"$relevant"

if [ -z "$blocked" ]; then
  echo "plan gate skipped by trailer for every changed source file"
  exit 0
fi

echo "source changed with no approved plan in this branch:"
printf '%s' "$blocked" | sed 's/^/  /'
echo
echo "Run /spec then /plan, and have a human set 'Status: Approved' in work/<slug>/plan.md."
echo "To skip a file deliberately, the commit that touches it carries '$TRAILER <reason>'."
exit 1
