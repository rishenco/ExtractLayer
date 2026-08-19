# 0009. Transport

Date: 2026-08-17 Status: Accepted

## Context

The web UI and HTTP clients need an API; agents need MCP. Two independent protocols would double the cost of every capability and let the surfaces drift apart.

## Decision

REST is the only main communication protocol — resource-oriented, in `transport`, emitting an OpenAPI document the UI generates types from. MCP duplicates the REST functionality as a facade for agents: one read-write endpoint whose tools mirror the REST capabilities, over the same `transport.dependencies` protocols. `transport.dto` holds the one JSON representation both emit, so a field cannot appear on one surface and not the other, and domain errors surface identically on both.

FastAPI builds the REST side. Starlette, uvicorn and pydantic already ship transitively with the `mcp` SDK, so the marginal dependency is small, and it replaces request validation that would otherwise be hand-written.

One process serves both transports on one port, `API_PORT`: REST at the root, MCP mounted at `/mcp`.

## Consequences

A capability added to a service reaches both surfaces only if both transports expose it; nothing enforces the mirror beyond the tests, so a tool added to one and forgotten in the other is a real failure mode.

One port to expose. Splitting the transports onto separate ports stays available later — it is a composition-root change, not a design change.

The layer contract holds for both: `transport` imports `domain` and its own dependencies, never `service` or `repo`.
