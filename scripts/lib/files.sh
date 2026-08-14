#!/usr/bin/env bash

EL_CODE_EXT="go ts tsx js jsx mjs cjs py rb rs java kt sql sh"
EL_SKIP_DIRS='(^|/)(node_modules|vendor|dist|build|\.next|target)/|^(work|docs)/'

el_repo_files() {
  if [ -n "${EL_FILE_LIST:-}" ]; then
    cat "$EL_FILE_LIST"
  elif git rev-parse --git-dir >/dev/null 2>&1; then
    {
      git -c core.quotePath=false ls-files
      git -c core.quotePath=false ls-files --others --exclude-standard
    } | sort -u
  else
    find . -type f -not -path './.git/*' | sed 's|^\./||' | sort -u
  fi
}

el_filter_ext() {
  local exts="$1" f ext
  while IFS= read -r f; do
    ext="${f##*.}"
    [ "$ext" = "$f" ] && continue
    case " $exts " in *" $ext "*) printf '%s\n' "$f" ;; esac
  done
}

el_code_files() {
  el_repo_files | el_filter_ext "$EL_CODE_EXT" | grep -vE "$EL_SKIP_DIRS" || true
}

el_is_generated() {
  local f="$1"
  case "$f" in
    *.gen.*|*.generated.*|*.pb.go|*_pb2.py|*.d.ts) return 0 ;;
  esac
  head -n 5 "$f" 2>/dev/null | grep -q 'DO NOT EDIT'
}

el_any_exists() {
  local p
  for p in "$@"; do [ -e "$p" ] && return 0; done
  return 1
}

el_line_count() {
  awk 'END { print NR }' "$1"
}

el_workspaces() {
  el_repo_files \
    | grep -E '(^|/)(package\.json|go\.mod|pyproject\.toml)$' \
    | grep -vE "$EL_SKIP_DIRS" \
    | sort -u
}

el_linted_dirs() {
  local manifest dir
  while IFS= read -r manifest; do
    [ -n "$manifest" ] || continue
    dir="$(dirname "$manifest")"
    case "$(basename "$manifest")" in
      package.json)
        el_any_exists "$dir"/eslint.config.{js,mjs,cjs,ts} "$dir"/.eslintrc.{js,cjs,json,yml,yaml} \
          && printf '%s\n' "$dir"
        ;;
      pyproject.toml) grep -q 'tool.ruff' "$manifest" 2>/dev/null && printf '%s\n' "$dir" ;;
      go.mod) el_any_exists "$dir"/.golangci.{yml,yaml,toml,json} && printf '%s\n' "$dir" ;;
    esac
  done < <(el_workspaces)
}

el_drop_linted() {
  local dirs f d keep
  dirs="$(el_linted_dirs)"
  [ -z "$dirs" ] && { cat; return 0; }
  while IFS= read -r f; do
    keep=1
    while IFS= read -r d; do
      [ -n "$d" ] || continue
      [ "$d" = "." ] && { keep=0; break; }
      case "$f" in "$d"/*) keep=0; break ;; esac
    done <<<"$dirs"
    [ "$keep" -eq 1 ] && printf '%s\n' "$f"
  done
}

el_base_ref() {
  local ref
  for ref in ${GITHUB_BASE_REF:+"origin/$GITHUB_BASE_REF"} origin/main main; do
    if git rev-parse --verify --quiet "$ref" >/dev/null 2>&1; then
      git merge-base HEAD "$ref" 2>/dev/null && return 0
    fi
  done
  return 1
}

el_changed_files() {
  if [ -n "${EL_CHANGED_LIST:-}" ]; then
    sort -u "$EL_CHANGED_LIST"
    return 0
  fi
  local base
  base="$(el_base_ref)" || return 1
  {
    git -c core.quotePath=false diff --name-only "$base"...HEAD
    git -c core.quotePath=false diff --name-only HEAD
    git -c core.quotePath=false ls-files --others --exclude-standard
  } 2>/dev/null | sort -u
}
