#!/usr/bin/env bash

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

found=0

add_file() {
  mkdir -p "$(dirname "$WORK/$1")"
  printf '%s\n' "$2" >"$WORK/$1"
}

fixture() {
  add_file "$1" "$2"
  printf '%s\n' "$WORK/$1" >"$WORK/list"
}

changed() { printf '%s\n' "$@" >"$WORK/changed"; }

expect() {
  local gate="$1" want="$2" name="$3" got
  EL_FILE_LIST="$WORK/list" "./scripts/gates/$gate" >/dev/null 2>&1
  got=$?
  [ "$got" -eq "$want" ] && return 0
  found=1
  printf '%s: %s exited %s, expected %s\n' "$name" "$gate" "$got" "$want"
}

expect_silent_about() {
  local gate="$1" pattern="$2" name="$3" out
  out="$(EL_FILE_LIST="$WORK/list" "./scripts/gates/$gate" 2>&1)"
  grep -qE "$pattern" <<<"$out" || return 0
  found=1
  printf '%s: %s still reports %s\n' "$name" "$gate" "$pattern"
}
