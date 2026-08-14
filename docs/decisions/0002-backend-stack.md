# 0002. Backend stack

Date: 2026-08-14
Status: Proposed

## Context

The UI is TypeScript/React. The backend language is open between Go, Python and TypeScript.
The choice is blocking: `scripts/gates/50-architecture.sh` and `60-workspaces.sh` cannot
enforce anything against a workspace that does not exist, so until it is made, the backend
half of the definition of done is empty.

The decision is load-bearing beyond preference. It fixes the boundary linter
(`go-arch-lint`, `import-linter`, `dependency-cruiser`), the type-checking strictness
available, and whether UI and backend can share types.

## Decision

Undecided. To be made before the first backend commit.

## Consequences

The layer map in `docs/architecture.md` is written stack-independently and applies whichever
way this resolves. Superseding this ADR is the only way to record the choice; the gates read
the resulting config files, not this document.
