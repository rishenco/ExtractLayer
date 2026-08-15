#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
unset EL_FILE_LIST EL_CHANGED_LIST

QUIET=0
LIST=0
for arg in "$@"; do
  case "$arg" in
    --quiet) QUIET=1 ;;
    --list) LIST=1 ;;
    *) echo "usage: check.sh [--quiet] [--list]" >&2; exit 64 ;;
  esac
done

shopt -s nullglob
GATES=(scripts/gates/*.sh)
shopt -u nullglob

if [ ${#GATES[@]} -eq 0 ]; then
  echo "no gates in scripts/gates/ — the definition of done is empty" >&2
  exit 1
fi

if [ ! -x scripts/gates/05-selftest.sh ]; then
  echo "scripts/gates/05-selftest.sh is missing or not executable — the gates are unverified" >&2
  exit 1
fi

if [ "$LIST" -eq 1 ]; then
  for gate in "${GATES[@]}"; do
    printf '%-28s %s\n' "$(basename "$gate" .sh)" "$("$gate" --describe 2>/dev/null)"
  done
  exit 0
fi

failed=()
for gate in "${GATES[@]}"; do
  name="$(basename "$gate" .sh)"
  output="$("$gate" 2>&1)"
  status=$?
  if [ $status -ne 0 ]; then
    failed+=("$name")
    printf 'FAIL %s\n' "$name"
    [ -n "$output" ] && printf '%s\n' "$output" | sed 's/^/     /'
  elif [ "$QUIET" -eq 0 ]; then
    printf 'ok   %s\n' "$name"
    [ -n "$output" ] && printf '%s\n' "$output" | sed 's/^/     /'
  fi
done

if [ ${#failed[@]} -gt 0 ]; then
  printf '\n%d gate(s) failed: %s\n' "${#failed[@]}" "${failed[*]}" >&2
  exit 1
fi

[ "$QUIET" -eq 0 ] && printf '\nall gates pass\n'
exit 0
