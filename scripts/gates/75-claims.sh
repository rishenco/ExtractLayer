#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh

[ "${1:-}" = "--describe" ] && { echo "Every claim about the work is audited and reproduced."; exit 0; }

changed="$(el_changed_files)" || {
  echo "no base ref to compare against, so this gate can verify nothing"
  echo "  fetch the default branch; CI needs actions/checkout with fetch-depth: 0"
  exit 1
}
[ -z "$changed" ] && exit 0

relevant="$(printf '%s\n' "$changed" | el_filter_ext "$EL_CODE_EXT" | grep -vE "$EL_SKIP_DIRS" || true)"
[ -z "$relevant" ] && exit 0

blocked="$(printf '%s\n' "$relevant" | el_blocked_after_trailer)"
[ -z "$blocked" ] && exit 0

ledgers=""
while IFS= read -r f; do
  case "$f" in
    work/*/claims.md|*/work/*/claims.md) [ -f "$f" ] && ledgers+="$f"$'\n' ;;
  esac
done < <(printf '%s\n' "$changed")

if [ -z "$ledgers" ]; then
  echo "source changed with no claims ledger:"
  printf '%s\n' "$blocked" | sed 's/^/  /'
  echo
  echo "Write work/<slug>/claims.md, then have the claim-auditor subagent reproduce each claim."
  echo "An unaudited claim is the hallucination this gate exists to catch."
  exit 1
fi

found=0
while IFS= read -r ledger; do
  [ -n "$ledger" ] || continue
  claims="$(grep -c '^## C' "$ledger" || true)"
  verdicts="$(grep -cE '^Verdict:[[:space:]]*(SUPPORTED|UNSUPPORTED|FALSE)[[:space:]]*$' "$ledger" || true)"
  bad="$(grep -nE '^Verdict:[[:space:]]*(UNSUPPORTED|FALSE)[[:space:]]*$' "$ledger" || true)"

  stray="$(grep -nvE '^(## C[0-9]+|Claim:|Evidence:|Verify:|Verdict:)' "$ledger" | grep -vE '^[0-9]+:$' || true)"
  selfref="$(grep -nE '^Evidence:.*(this ledger|this file|passes once|once the audit|after the audit)' "$ledger" || true)"

  [ "$claims" -eq 0 ] && { found=1; echo "$ledger: no claims, so nothing was audited"; continue; }
  [ -n "$stray" ] && {
    found=1
    printf '%s\n' "$stray" | sed "s|^|$ledger: not part of a claim block: |"
  }
  [ -n "$selfref" ] && {
    found=1
    printf '%s\n' "$selfref" | sed "s|^|$ledger: evidence describes the ledger, not the tree: |"
  }
  [ "$verdicts" -ne "$claims" ] && {
    found=1
    echo "$ledger: $claims claims but $verdicts verdicts — the audit did not finish"
  }
  [ -n "$bad" ] && {
    found=1
    printf '%s\n' "$bad" | sed "s|^|$ledger: unresolved |"
  }
done <<<"$ledgers"

[ "$found" -eq 0 ] && exit 0
echo
echo "Fix what is false, or withdraw the claim. A claim nobody could reproduce does not ship."
echo "A ledger is claim blocks and verdicts; evidence points at the tree, not at the ledger."
exit 1
