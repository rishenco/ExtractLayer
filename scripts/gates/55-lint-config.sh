#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Workspaces lint with real parsers, not the repo-level floor."; exit 0; }

manifests="$(el_workspaces)"
[ -z "$manifests" ] && { echo "no workspace yet — the repo-level floor is all there is"; exit 0; }

found=0
while IFS= read -r manifest; do
  dir="$(dirname "$manifest")"
  case "$(basename "$manifest")" in
    package.json)
      el_any_exists "$dir"/eslint.config.{js,mjs,cjs,ts} "$dir"/.eslintrc.{js,cjs,json,yml,yaml} && continue
      found=1
      echo "$dir: no eslint config"
      echo "  enable no-inline-comments, no-warning-comments and max-lines, then this"
      echo "  workspace stops being scanned by 10-comments and 20-budgets"
      ;;
    pyproject.toml)
      grep -q 'tool.ruff' "$manifest" && continue
      found=1
      echo "$dir: no [tool.ruff]"
      echo "  enable ERA001 and the file-length rule, then this workspace stops being"
      echo "  scanned by 10-comments and 20-budgets"
      ;;
    go.mod)
      el_any_exists "$dir"/.golangci.{yml,yaml,toml,json} && continue
      found=1
      echo "$dir: no .golangci config"
      echo "  enable the comment and function-length linters, then this workspace stops"
      echo "  being scanned by 10-comments and 20-budgets"
      ;;
  esac
done <<<"$manifests"

if ! el_any_exists .vale.ini vale.ini; then
  found=1
  echo "no .vale.ini — prose is still checked by a hand-written phrase list"
  echo "  move the phrases in 30-slop.sh into a Vale style and delete them from the gate"
fi

[ "$found" -eq 0 ] && exit 0
echo
echo "The repo-level gates guess with regexes. These tools parse. See docs/decisions/0003."
exit 1
