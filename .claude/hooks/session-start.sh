#!/usr/bin/env bash
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

echo "Definition of done: make check. Loop: /spec -> /plan -> approval -> /build -> review -> PR."

[ -f docs/vision.md ] || echo "docs/vision.md is missing. Run /vision before product work, or ask the human to."

shopt -s nullglob
for dir in work/*/; do
  slug="$(basename "$dir")"
  if [ -f "$dir/plan.md" ]; then
    status="$(grep -m1 '^Status:' "$dir/plan.md" 2>/dev/null | sed 's/^Status:[[:space:]]*//')"
    echo "open work: $slug (plan ${status:-unknown})"
  elif [ -f "$dir/spec.md" ]; then
    echo "open work: $slug (spec only, no plan)"
  fi
done
exit 0
