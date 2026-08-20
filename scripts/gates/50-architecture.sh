#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Every workspace declares enforced layer boundaries."; exit 0; }

manifests="$(el_workspaces)"
[ -z "$manifests" ] && { echo "no workspace yet — boundaries unenforced"; exit 0; }

found=0
while IFS= read -r manifest; do
  dir="$(dirname "$manifest")"
  case "$(basename "$manifest")" in
    package.json)
      el_any_exists "$dir"/.dependency-cruiser.{js,cjs,mjs,json} && continue
      found=1
      echo "$dir: no .dependency-cruiser config — layer boundaries are unenforced"
      echo "  encode docs/architecture.md as forbidden rules with severity error"
      ;;
    go.mod)
      el_any_exists "$dir"/.go-arch-lint.{yml,yaml} && continue
      found=1
      echo "$dir: no .go-arch-lint config — layer boundaries are unenforced"
      echo "  encode docs/architecture.md as components and their allowed deps"
      ;;
    pyproject.toml)
      grep -q 'tool.importlinter' "$manifest" && continue
      found=1
      echo "$dir: no [tool.importlinter] contracts — layer boundaries are unenforced"
      echo "  add layered contracts matching docs/architecture.md"
      ;;
  esac
done <<<"$manifests"

[ "$found" -eq 0 ] && exit 0
echo
echo "A layer map nothing enforces is a suggestion."
exit 1
