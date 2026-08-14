#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Behaviour changes reach CHANGELOG.md."; exit 0; }

grep -q '^## \[Unreleased\]' CHANGELOG.md 2>/dev/null || {
  echo "CHANGELOG.md is missing an '## [Unreleased]' section"
  exit 1
}

changed="$(el_changed_files)" || {
  echo "no base ref to compare against, so this gate can verify nothing"
  echo "  fetch the default branch; CI needs actions/checkout with fetch-depth: 0"
  exit 1
}
[ -z "$changed" ] && exit 0

relevant="$(printf '%s\n' "$changed" | el_filter_ext "$EL_CODE_EXT" | grep -vE "$EL_SKIP_DIRS" || true)"
[ -z "$relevant" ] && exit 0

printf '%s\n' "$changed" | grep -qx 'CHANGELOG.md' && exit 0

echo "source changed but CHANGELOG.md did not:"
printf '%s\n' "$relevant" | sed 's/^/  /'
echo
echo "Add the user-visible effect under '## [Unreleased]'."
exit 1
