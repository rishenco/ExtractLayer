#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
. scripts/lib/files.sh

failed=0

while IFS= read -r manifest; do
  [ -n "$manifest" ] || continue
  dir="$(dirname "$manifest")"
  echo "installing $dir"
  case "$(basename "$manifest")" in
    pyproject.toml)
      out="$( cd "$dir" && pip install -e '.[dev]' 2>&1 )" || failed=1
      printf '%s\n' "$out"
      case "$out" in
        *"does not provide the extra"*)
          failed=1
          echo "$dir: no 'dev' extra — its lint, type and test tooling is not installed"
          ;;
      esac
      ;;
    package.json)
      ( cd "$dir" && npm ci ) || failed=1
      ;;
  esac
done < <(el_workspaces)

exit "$failed"
