# 0010. Postgres; docker compose bootstraps the project

Date: 2026-08-18 Status: Accepted

## Context

Background jobs are rows that concurrently running workers claim and lease (`docs/decisions/0011-jobs-claimed-from-the-database.md`). Honest concurrent claiming needs row locking with `SELECT ... FOR UPDATE SKIP LOCKED`; an embedded store such as SQLite serializes writers and has no equivalent, so claiming on top of one means building a lock protocol the database should provide.

## Decision

Postgres is the only supported store, from development through production. Tables live in the `extractlayer` schema; ids are serials; timestamps are `timestamptz`; every table carries `created_at`/`updated_at`. Migrations run on yoyo (ADR 0008), which speaks plain SQL to Postgres.

`docker compose up` is the bootstrap path: a `docker-compose.yml` at the repository root brings up Postgres and the app, so a fresh clone reaches a running system with one command and no local database install. Tests run against the same Postgres, not a substitute engine — a test double for the store proves nothing about the claim queries.

## Consequences

Deployment needs a database server; compose carries that cost for development and self-hosting. In exchange the job substrate gets real row locking, concurrent workers, and `jsonb` for payloads, checkpoints and progress. One engine, deliberately: a second supported store would mean the gate suite proves only one of them.
