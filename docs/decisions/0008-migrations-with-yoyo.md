# 0008. Schema changes are migrations, run by yoyo

Date: 2026-08-17 Status: Accepted

## Context

Creating tables by re-running DDL on startup works exactly once: it cannot alter a column, cannot record what a database has already had applied, and cannot tell a fresh store from a stale one — the first schema change becomes a hand-written, unversioned fix.

## Decision

Schema changes are numbered SQL migrations in `extractlayer/repo/migrations`, applied by `yoyo-migrations` when the service starts. Migrations are the only way the schema changes. yoyo over Alembic because it applies plain SQL and does not require SQLAlchemy, which this repository does not use.

## Consequences

The store carries its own version, so a deployment can be upgraded rather than rebuilt, and a test database is built the same way production is. Rollbacks are available per migration but unwritten so far; the first destructive migration is where that debt comes due.
