.PHONY: check gates

check:
	@scripts/check.sh

gates:
	@scripts/check.sh --list
