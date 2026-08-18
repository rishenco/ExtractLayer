# Lessons

Rules learned from real defects that could not be made executable. Everything here is debt: each line is a rule a human has to remember instead of a check that fails the build.

Added by `/compound`, and only after a test, a gate, and a hook were each ruled out.

Format: one line, imperative, with the change that taught it.

## Open

- In-repo approval markers are forgeable by an agent: `Status: Approved` and `Skips-plan-gate:` are both writable by whoever writes the code. `70-approved-plan.sh` makes intent traceable, not enforced. The non-forgeable gate is the pull request review on GitHub, so branch protection requiring a human approval is what actually holds — added while bootstrapping the loop.
- Write claims after the code is committed, not before. `el_trailer_exempt` never exempts a file with uncommitted changes, so a ledger written on a dirty tree makes claims about a state no gate can reach — found when the auditor refuted the first ledger written here.
- `10-comments.sh` matches per line, so a `#` or a URL inside a heredoc, a Go raw string, or a Python triple-quoted string reads as a comment and fails the gate. Move comment linting to each workspace linter, which parses instead of guessing, as soon as a stack lands — found by adversarial review of the gate itself.
- A service method nothing calls — no interface, no other service, no test — is unrequested scope; delete it before review. A `vulture` gate is the executable successor if this recurs — found when review caught a dead `assign_split` in the extractor core.
- When an approved plan supersedes a spec section, amend the spec in the same commit; the spec is what later reviews trace to — found when the core shipped its job runner in `application` while the spec still said `infrastructure`.
- A cache with no eviction bound is a leak. Bound it at construction or do not build it — found when review priced the embedding cache at a gigabyte of vectors per long-lived process.
- Moving a workspace manifest changes which files the repo-level floor scans: `el_drop_linted` retires the floor only for the extensions that workspace's linter actually parses. A workspace at the repository root silently retired it for every shell script until the flattening review caught it.
- `ruff` does not enforce this repo's no-comments rule — `ERA001` flags commented-out code, not prose — so a prose comment in a `.py` file is caught by nobody once the floor recedes for that workspace. Weigh that before treating a linted workspace as fully covered.
- Generated data only tests what it can generate: a property test whose fixtures cannot produce the failing input passes whatever the code does. Check the generator's range against the invariant, not just the assertion — found when embedding vectors built from unsigned bytes could never reach the cosine clamp they were meant to pin.
- Prose in a claims ledger never states an audit outcome; only an auditor-written `Verdict:` line does — found when a preamble said six claims were re-audited before any verdict existed.
- A transport never defaults a missing client field: absent is an error or a declared optional — found when the MCP `add_pairs` tool turned a misspelled `derived_values` key into an empty dict and landed all-null pairs labeled human.
- A wire field or column is named in exactly one doc; other docs point, never restate — found when `process` took `source_columns` in one doc and `source_values` in another, and ADR 0011's column list drifted from the storage doc.
- Removing an implementation re-opens every doc that says "shipped": a sequencing section states what to build next, not what once existed — found when the deleted extractor core stayed "shipped first" in the build order.
- A committed doc outside `work/` describes the product as it stands, to a reader with no access to how it got that way. `35-narration.sh` floors the giveaway phrasings; narration worded past the floor only review can see — found when a docs rewrite had to strip the project's own build story from every ADR, the changelog, and the README.
