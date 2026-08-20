# 0012. The runtime is async, on psycopg 3

Date: 2026-08-19 Status: Accepted

## Context

One process serves REST and MCP on `API_PORT` and runs the job claimer (`docs/architecture.md`). The claimer ticks about every two seconds per claimed job to renew a lease and pull a signal (`docs/decisions/0011-jobs-claimed-from-the-database.md`), and the work between ticks is dominated by waiting on Postgres and on model providers. Nothing in the design is CPU-bound. FastAPI and the `mcp` SDK are both async-native, so a sync core would push every route and every tick through a thread pool, and the in-process claimer would become a thread rather than a task.

The driver choice follows from that, and is constrained by yoyo (ADR 0008), which runs migrations synchronously.

## Decision

The runtime is `async` throughout: services, repositories and transports are coroutine functions, and the claimer is a task on the same event loop.

Postgres is reached through psycopg 3, which offers both an async and a sync API from one package and one connection string. Async connections serve requests through `psycopg_pool.AsyncConnectionPool`; yoyo applies migrations over the same driver through its `postgresql+psycopg` backend.

## Consequences

One driver covers both the request path and the migration path, so a connection string means the same thing everywhere and no second driver is installed to run migrations.

Blocking work is now a defect rather than a slowdown: a synchronous call in a coroutine stalls the claimer and every in-flight request together. Anything genuinely CPU-bound has to be moved off the loop deliberately.

Reversing this means replacing the pool, rewriting every `async def` and rehoming the claimer in a thread. The driver alone is cheaper to reverse: asyncpg would serve the request path, at the cost of a second driver for yoyo, which is what this decision avoids.
