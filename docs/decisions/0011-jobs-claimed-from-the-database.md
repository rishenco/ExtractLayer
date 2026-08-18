# 0011. Jobs are database rows that workers claim and lease

Date: 2026-08-18
Status: Accepted

## Context

GEPA training, evals and dataset filling must be watched live, survive restarts, and
take stop/kill signals; jobs must not require an extractor, so the same substrate can
carry system maintenance. An in-process runner fails all of it: a restart loses every
running job, progress is invisible until the end, and workers cannot outnumber the
serving process.

## Decision

A job is a row — columns in `docs/architecture.md`; the ones this decision turns on are
`checkpoint`, `progress`, `status`, `signal`, `claim_id` and `claimed_at`. The job
service owns the job tables: spawning is a call on it through a dependency the caller
declares, and the service inserts the row, claims pending rows and runs them. Between
processes, the table is the only channel.

**Claiming.** A worker claims a row by writing a fresh `claim_id` and `claimed_at`
(`FOR UPDATE SKIP LOCKED`). The lease alone decides claimability: an unsettled row whose
`claimed_at` is null or older than the TTL is claimable. `pending` and `running` are read
off `claimed_at` rather than stored, so a job whose worker died comes back to the queue
with no transition written for it. Every write a worker makes is fenced with
`WHERE claim_id = <its own>`, so a worker that lost its lease can no longer corrupt the
row it thinks it owns.

**The tick.** A running job ticks on a constant short interval (~2s): renew `claimed_at`,
read `signal`, write `progress` — a small JSON the UI polls to watch the job live.

**Checkpoints.** Saved at logical boundaries of the work, not on the tick; they may be
large. A resumed job starts from its checkpoint, and handlers are written idempotently so
a replayed step is harmless. `stop` is the graceful signal — halt at the next tick, keep
the checkpoint, stay resumable: resuming clears the settled status and the claim, keeps the
checkpoint, and a claimer picks the row up again. `kill` ends the job for good. A claimer
reads `signal` before it starts work, so a signal on an unclaimed row settles at the claim
rather than waiting for a tick no worker is running.

**Ownership.** The job service alone writes `jobs`, `job_logs` and `extractor_jobs`.
Jobs carrying an extractor's work hold the `extractor_id` in `payload`;
`extractor_jobs` mirrors the link as a query index — the payload is authoritative, the
duplication accepted. System-owned jobs simply have neither. `job_logs` is the
append-only trail; `progress` is latest-value.

## Consequences

Workers scale by running more claimers, and the API can spawn work while no worker is
alive. The costs are honest ones: handlers must be written for resumption and idempotence
rather than assuming one clean run, the lease TTL bounds how long a dead worker's job waits
before another claimer takes it, and a zombie worker wastes compute after losing its lease
even though fencing keeps it from writing. Requires Postgres
(`docs/decisions/0010-postgres.md`).
