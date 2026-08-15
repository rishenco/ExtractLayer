#!/usr/bin/env bash
set -uo pipefail

input="$(cat 2>/dev/null || true)"
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

. scripts/lib/files.sh

dirty="$( { git diff --name-only HEAD; git ls-files --others --exclude-standard; } 2>/dev/null | head -n 1 )"
if base="$(el_base_ref)"; then
  ahead="$(git rev-list --count "$base"..HEAD 2>/dev/null || echo 0)"
  [ -z "$dirty" ] && [ "$ahead" = "0" ] && exit 0
fi

out="$(./scripts/check.sh --quiet 2>&1)" && exit 0

if grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true' <<<"$input"; then
  printf '{"systemMessage":"make check is still failing. The agent was told to say so rather than keep retrying."}\n'
  exit 0
fi

{
  echo "make check fails, so this work is not done. Fix it, or say plainly in your reply that you are leaving it red and what is failing."
  echo
  printf '%s\n' "$out"
} >&2
exit 2
