#!/usr/bin/env bash
set -uo pipefail

input="$(cat 2>/dev/null || true)"
payload="${input//\\\"/\"}"

grep -qE '"(is_error|isError)"[[:space:]]*:[[:space:]]*true' <<<"$payload" && exit 0

url="$(grep -oE 'https://github\.com/[^"/[:space:]]+/[^"/[:space:]]+/pull/[0-9]+' <<<"$payload" | head -n 1)"
[ -n "$url" ] || exit 0

owner="$(cut -d/ -f4 <<<"$url")"
repo="$(cut -d/ -f5 <<<"$url")"
number="$(cut -d/ -f7 <<<"$url")"

{
  echo "$url is open and no session is listening to it."
  echo "Call subscribe_pr_activity with owner=$owner repo=$repo pullNumber=$number, then end the turn."
  echo "CI failures and review comments wake this session as they arrive; polling with sleep does not."
} >&2
exit 2
