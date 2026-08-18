# 0005. Backend is Python

Date: 2026-08-16
Status: Accepted

## Context

The backend language was open between Go, Python and TypeScript. The deciding
constraint: the training path — GEPA-style optimization of small models — lives in the
Python ecosystem, and a two-language product would put a service boundary between the
core and its trainers.

## Decision

The backend is Python, over Go and TypeScript. The core service and future training
workers share the language. Layer boundaries from `docs/architecture.md` are enforced
with `import-linter`.

## Consequences

A trainer imports the same domain code the core service uses instead of calling across a
service boundary. UI and backend do not share types, so the API contract carries them
explicitly. Deployment means a Python runtime or a container image, not a static binary.
Reversing this takes a new ADR and a rewrite of whatever backend exists by then; the
layer map is stack-independent and survives either way.
