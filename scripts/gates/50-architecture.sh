#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Every workspace declares layer boundaries; Python's hold."; exit 0; }

manifests="$(el_workspaces)"
[ -z "$manifests" ] && { echo "no workspace yet — boundaries unenforced"; exit 0; }

found=0
PROBE=""

fail() { found=1; printf '%s\n' "$*"; }

clean_probe() { [ -n "$PROBE" ] && rm -f "$PROBE"; PROBE=""; return 0; }
trap clean_probe EXIT

while IFS= read -r manifest; do
  dir="$(dirname "$manifest")"
  case "$manifest" in
    /*) absolute="$manifest" ;;
    *) absolute="$PWD/$manifest" ;;
  esac
  case "$(basename "$manifest")" in
    package.json)
      el_any_exists "$dir"/.dependency-cruiser.{js,cjs,mjs,json} && continue
      fail "$dir: no .dependency-cruiser config — layer boundaries are unenforced"
      echo "  encode docs/architecture.md as forbidden rules with severity error"
      ;;
    go.mod)
      el_any_exists "$dir"/.go-arch-lint.{yml,yaml} && continue
      fail "$dir: no .go-arch-lint config — layer boundaries are unenforced"
      echo "  encode docs/architecture.md as components and their allowed deps"
      ;;
    pyproject.toml)
      if ! grep -q 'tool.importlinter' "$manifest"; then
        fail "$dir: no [tool.importlinter] contracts — layer boundaries are unenforced"
        echo "  add layered contracts matching docs/architecture.md"
        continue
      fi
      [ -n "$(find -L "$dir" -name '*.py' -not -path '*/.venv/*' -print -quit 2>/dev/null)" ] || continue
      if ! command -v lint-imports >/dev/null 2>&1; then
        fail "$dir: import-linter is not installed — the declared layer map is unchecked"
        continue
      fi
      exempted="$(el_exempted_imports "$absolute")"
      if [ -n "$exempted" ]; then
        fail "$dir: ignore_imports in $(tr '\n' ' ' <<<"$exempted")"
        echo "  an exempted import is a boundary nothing holds"
        continue
      fi
      report="$(el_run_in "$dir" lint-imports --no-cache 2>&1)" || {
        fail "$dir: the declared layer map does not hold"
        printf '%s\n' "$report" | sed 's/^/  /'
        continue
      }
      unanalysed="$(el_run_in "$dir" el_unanalysed_modules "$absolute" 2>/dev/null)"
      listed=$?
      if [ "$listed" -ne 0 ]; then
        fail "$dir: could not list the modules import-linter analysed"
        continue
      fi
      if [ -n "$unanalysed" ]; then
        fail "$dir: import-linter never analysed $(tr '\n' ' ' <<<"$unanalysed")"
        echo "  a module it never sees is a module no contract holds"
        continue
      fi
      probes="$(el_boundary_probes "$absolute")"
      if [ -z "$probes" ]; then
        fail "$dir: no layers contract puts a package below another layer"
        echo "  nothing here forbids an import, so the contracts constrain nothing"
        continue
      fi
      while IFS="$(printf '\t')" read -r PROBE above dotted; do
        printf 'import %s\n' "$above" >"$PROBE"
        refusal="$(el_run_in "$dir" lint-imports --no-cache 2>&1)"
        refused=$?
        clean_probe
        [ "$refused" -ne 0 ] \
          && grep -qE "^[[:space:]]*- $dotted -> $above \(l\.[0-9]+\)" <<<"$refusal" \
          && continue
        fail "$dir: no contract refuses $dotted importing $above"
        echo "  the layers are not held apart by anything import-linter reports broken"
      done <<<"$probes"
      ;;
  esac
done <<<"$manifests"

[ "$found" -eq 0 ] && exit 0
echo
echo "A layer map nothing enforces is a suggestion."
exit 1
