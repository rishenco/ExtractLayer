# Architecture

The layer map exists so that "where does this go" has one answer, and so that a fix landing
at the wrong layer fails the build instead of a review.

## The dependency rule

Dependencies point inward. An inner layer never imports an outer one.

```
interface  →  application  →  domain  ←  infrastructure
```

| Layer | Holds | May import | Never |
| --- | --- | --- | --- |
| `domain` | Entities, invariants, port interfaces | nothing in this repo | I/O, frameworks, SQL, HTTP |
| `application` | Use cases orchestrating domain via ports | `domain` | concrete adapters, transport types |
| `infrastructure` | Adapters implementing domain ports: DB, queues, external APIs | `domain` | `application`, `interface` |
| `interface` | HTTP handlers, CLI, jobs — transport in, DTO out | `application`, `domain` | `infrastructure` directly |

Wiring lives at the composition root (`main`, `cmd/`, the server entrypoint). It is the only
place allowed to name a concrete adapter.

## UI

```
pages  →  features  →  entities  →  shared
```

A slice imports only strictly lower slices. Cross-imports between two features go through
`entities` or `shared`, never sideways. Server-state access is confined to `features` and
below; components at `pages` receive data, they do not fetch it.

## Where a fix goes

Fix the layer that owns the violated invariant. Symptoms surface outward: a bad value in a page
usually originates in `domain` or in the adapter that produced it. Patching the render is a
workaround, allowed only when labelled as one with the real fix proposed alongside.

## Enforcement

The rule is executable, not advisory. Every workspace declares its boundaries in a config the
linter reads, and `scripts/gates/50-architecture.sh` fails when a workspace has none:

| Workspace | Tool | Config |
| --- | --- | --- |
| TypeScript | `dependency-cruiser` | `.dependency-cruiser.js` |
| Go | `go-arch-lint` | `.go-arch-lint.yml` |
| Python | `import-linter` | `[tool.importlinter]` in `pyproject.toml` |

Changing a boundary means changing the config in the same commit as the code, which makes the
change visible in review instead of silent.

A config that exists but forbids nothing satisfies the gate and enforces nothing. The rules are
the deliverable, not the file.

## Status

No workspace exists yet, so nothing here is enforced. The backend stack is undecided —
`docs/decisions/0002-backend-stack.md`. Confirm or replace this map when the first workspace
lands and the boundaries are written into its linter; superseding it means a new ADR.
