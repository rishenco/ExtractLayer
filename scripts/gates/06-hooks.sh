#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

[ "${1:-}" = "--describe" ] && { echo "Hooks still fire, and only when they should."; exit 0; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

found=0

mkdir -p "$WORK/hook/docs" "$WORK/hook/work/planned" "$WORK/hook/work/unplanned"
: >"$WORK/hook/docs/vision.md"
printf 'Status: Approved\n' >"$WORK/hook/work/planned/plan.md"
printf '## C1\n' >"$WORK/hook/work/unplanned/claims.md"
hook_out="$(CLAUDE_PROJECT_DIR="$WORK/hook" bash .claude/hooks/session-start.sh 2>/dev/null)"

grep -qx 'open work: planned (plan Approved)' <<<"$hook_out" || {
  found=1
  echo "session hook: does not report an approved plan"
}
grep -q 'unplanned' <<<"$hook_out" && {
  found=1
  echo "session hook: reports a slug with no plan as open work"
}
[ "$(grep -c '^open work:' <<<"$hook_out")" -eq 1 ] || {
  found=1
  echo "session hook: does not print exactly one state per slug"
}

pr_hook() {
  printf '%s' "$1" | bash .claude/hooks/pr-subscribe.sh 2>&1
}

opened='{"tool_name":"mcp__github__create_pull_request","tool_response":{"content":[{"type":"text","text":"{\\"html_url\\": \\"https://github.com/acme/widget/pull/7\\"}"}]}}'
pr_out="$(pr_hook "$opened")"
[ "$?" -eq 2 ] || {
  found=1
  echo "pr hook: does not stop the turn when a pull request was opened"
}
grep -q 'subscribe_pr_activity with owner=acme repo=widget pullNumber=7' <<<"$pr_out" || {
  found=1
  echo "pr hook: does not name the pull request it wants subscribed"
}

refused='{"tool_name":"mcp__github__create_pull_request","tool_response":{"is_error":true,"content":[{"type":"text","text":"A pull request already exists for acme:topic, see https://github.com/acme/widget/pull/7"}]}}'
pr_hook "$refused" >/dev/null
[ "$?" -eq 0 ] || {
  found=1
  echo "pr hook: fires when the pull request was refused"
}

pr_hook '{"tool_name":"mcp__github__create_pull_request","tool_response":{"content":[]}}' >/dev/null
[ "$?" -eq 0 ] || {
  found=1
  echo "pr hook: fires when no pull request url is present"
}

for hook in .claude/hooks/*.sh; do
  [ -x "$hook" ] || {
    found=1
    echo "hooks: $hook is not executable, so nothing can run it"
  }
  grep -q "$(basename "$hook")" .claude/settings.json || {
    found=1
    echo "hooks: $hook is not registered in .claude/settings.json"
  }
done

[ "$found" -eq 0 ] && exit 0
echo
echo "A hook that stopped firing enforces nothing."
exit 1
