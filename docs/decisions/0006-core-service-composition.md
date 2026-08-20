# 0006. Core service composition

Date: 2026-08-17 Status: Accepted

## Context

The core needs an LLM client, schema validation, a metric engine and two transports. ADR 0005 fixed the language; this fixes the parts.

## Decision

One Python workspace at the repository root, package `extractlayer`, laid out as the four layers of `docs/architecture.md` with the composition root at `extractlayer/main.py`. Boundaries are `import-linter` contracts in `pyproject.toml`, executed by a test so `pytest` enforces them.

- LLM calls go through OpenRouter using the `openai` SDK against the OpenRouter base URL.
- Schemas are JSON Schema draft 2020-12 validated with `jsonschema`; ExtractLayer metric configuration lives in a namespaced `x-el` keyword and is stripped before any LLM call.
- The metric engine uses `scipy` for optimal array assignment and `rapidfuzz` for string distance.
- The MCP endpoint is built from the official `mcp` SDK over the service layer.
- Storage is Postgres (0010); jobs are database rows claimed by workers (0011).

## Consequences

The `openai` SDK ties request shape to the OpenAI-compatible surface OpenRouter exposes; leaving OpenRouter means an adapter, not a domain change. Training and agentic work attach as new job kinds without changing the job shape.
