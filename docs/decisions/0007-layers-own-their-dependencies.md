# 0007. Layers own their dependencies, and the tree stays flat

Date: 2026-08-17 Status: Accepted

## Context

An interface can live with its implementations, in a shared inner layer, or with its consumer. The first couples the consumer to the implementation package; the second makes the layer that owns an interface different from the layer that needs it, so changing a consumer means editing a layer it does not own. The model here is the Go one: a consumer declares the narrow interface it needs, and implementations satisfy it without knowing it exists. Python's `Protocol` is structural, so this works without any import from implementation to interface. Hexagonal jargon calls these interfaces ports; the plainer word is dependencies, so the modules are named `dependencies` and the docs say dependency.

## Decision

The workspace is the repository root; the package is `extractlayer`. Layer directories are `domain`, `service`, `repo`, `transport` — flat, one entity per file.

Layers glue through `typing.Protocol`: every cross-layer interface is a structural protocol, satisfied by shape and checked by mypy — no ABCs, no inheritance, no runtime registration, no import from implementation to interface.

Consumers own their dependencies, declared in the file that consumes them rather than in a module of their own: a service declares the repository, model client or embedding client it needs beside itself, and a transport declares the service interfaces it drives beside itself. A protocol earns a module when a second file consumes it. `repo` implements the protocols `service` declares, structurally, importing nothing from them.

`domain` holds entities, their invariants and the schema's structure. Metric kinds, their configuration in `x-el` and the scoring engine are `service`.

One import-linter contract enforces it: `transport`, `service` and `repo` are siblings above `domain`, so none of them may import another. `extractlayer.main` is the composition root and the only module that names a concrete adapter.

## Consequences

A service can be read without leaving its layer: the interfaces it needs are declared beside it. Swapping an adapter touches the composition root only, and a test double satisfies a dependency by shape rather than by inheritance.

The cost is duplication by design: two layers that need the same collaborator declare it twice, and a change to a service signature changes the protocol the transport declares as well. That is the price of the sibling rule, which is what keeps the layers substitutable.

Nothing outside the composition root can reach `repo`, so accidental coupling to the store or to OpenRouter fails `pytest` rather than review.
