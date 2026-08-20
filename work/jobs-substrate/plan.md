# Jobs substrate

Status: Approved

## Problem / Intent

Nothing asynchronous exists. Gap-filling, evals, training and agentic drafting are all long work
a human must watch live, stop and resume, and none of it is buildable until the substrate under
it exists. ADR 0011 decided the mechanism — fenced leases, a tick, checkpoints — and not one line
of it is falsifiable today.

Afterwards: the three job tables behind a migration, a claimer inside the serving process working
unleased rows under a fenced lease, jobs read, signalled and log-read over REST, and a seam a job
kind attaches to.

Objections: two. Datasets and models were to come before jobs; jobs come first, because the core
is built on the job substrate and building it second retrofits every use case onto it. The engine
lives in `service/jobs/` and a kind's handler beside the service owning its logic, contradicting
ADR 0007's flat rule; ADR 0013 amends that rule rather than the layout bending to a sentence
written when a subject was one file.

## Criteria

- [ ] A1 `make check` passes: gates, `ruff`, `mypy`, `pytest`, layers contract and all.
- [ ] A2 `0002-jobs.sql` creates `jobs`, `job_logs` and `extractor_jobs` with the columns
      `docs/architecture.md:43` names, from an empty database, and re-applying changes nothing.
- [ ] A3 Claiming is exclusive and lease-bound: of two claimers racing one row, one wins; a row
      claimed under the TTL is not claimable, and is claimable again once `claimed_at` is older
      than it, with no status transition written for the row.
- [ ] A4 Fencing holds: once a second claimer takes a job, the first's writes change no row.
- [ ] A5 The tick renews the lease and publishes progress: while a handler runs, `claimed_at`
      advances and `GET /jobs/{id}` returns the progress the handler last wrote.
- [ ] A6 `stop` halts the handler at the next tick, settling `stopped` with the checkpoint kept;
      `resume` returns it to `running`, and the next claim restarts it from that checkpoint.
- [ ] A7 `kill` settles `killed`, and a killed job is never claimed again.
- [ ] A8 A signal on an unclaimed `running` row settles at the claim: a killed-then-claimed job
      reaches `killed` without its handler running.
- [ ] A9 Failure settles `error` and the claimer carries on to the next job: a handler that
      raises records its message, a kind with no handler records the kind.
- [ ] A10 Signalling is guarded: `stop` or `kill` on a terminal job, `resume` on a job that is
      not `stopped` or `error`, and an unknown signal are 422; an absent job is 404.
- [ ] A11 `GET /jobs` and `GET /jobs/{id}/logs` walk a seeded set once over `after_id` + `limit`,
      no row repeated or skipped, logs in append order.
- [ ] A12 `GET /extractors/{id}/jobs` returns exactly the jobs whose payload carries that
      extractor id, filters by kind and status, sorts by `created_at` or `duration` under a
      `<sort_column, id>` cursor, and a job spawned without one writes no `extractor_jobs` row.
- [ ] A13 The claimer runs inside the serving process: a job spawned against an app built by
      `build_app` reaches `done` through that app's own claimer, and shutdown stops it.

## Not doing

- Datasets, dataset rows, models and `serve`, and therefore every documented spawn route
  (`fill-gaps`, `train`, `eval`), their handlers, and `eval_scores`. No route spawns a job here.
- MCP tools mirroring the job routes.
- Retries, backoff, priorities, scheduled jobs, job deletion and log retention.
- A worker-only entrypoint: more claimers is the same process run again
  (`docs/architecture.md:86`), and one claimer works one job at a time.
- Filters or sorts on `GET /jobs`, which `docs/architecture.md:58` gives none.

## Research

- `docs/architecture.md:43` names every column of the three tables, the statuses, the claimable
  predicate and the ~2s tick; `:54` and `:58` the five routes; `:49` the cursor and error-code
  rules; `:86` the configuration list and the one-process rule.
- `docs/decisions/0011-jobs-claimed-from-the-database.md:13,15,17,19,23` fixes the claim and fence
  predicates, the tick's three writes, checkpoint and signal semantics, table ownership and
  handler idempotence. `0012:13` puts the claimer on the serving loop, `:21` says a synchronous
  call there stalls every request; `0010:13` forbids a substitute for Postgres.
- `docs/decisions/0007-layers-own-their-dependencies.md:11` "flat, one entity per file"; `:13` no
  runtime registration; `:15` a consumer declares its dependency beside itself, a protocol
  earning a module at the second consumer.
- Shape to follow: `service/extractors.py:13` and `transport/http.py:17` for the protocol seams;
  `repo/extractors.py:16,20,53,75` for `COLUMNS`, `class_row`, `Jsonb` and keyset paging;
  `main.py:16` for migrations, pool and lifespan; `transport/errors.py:15` for error-to-code
  mapping; `tests/conftest.py:26` for the per-test database.
- Two tests pin what this change grows: `tests/test_bootstrap.py:25` asserts the OpenAPI path set
  is exactly the two extractor paths, `tests/test_extractors_repo.py:47` asserts one migration
  file exists. `scripts/gates/10-comments.sh:8,22` fails any `--` line in `.sql`.

## Approach

The change lands in `service`, with `repo` and `transport` following the shape change 1 set.
`service/jobs/` holds the engine — job service, claimer, handler seam — since
`docs/architecture.md:72` puts jobs in `service` and the engine is three files. A kind's business
logic is not the engine's, so a handler is a file beside the service that owns it
(`service/extractors/` when fill-gaps lands), which is why `service/extractors.py` becomes
`service/extractors/service.py` now, while there is one file to move. The claimer is a task on
the serving loop, cancelled at shutdown; kinds reach it as a `Mapping[str, JobHandler]` passed at
`main.py`, the only module naming concrete parts. Fake kinds are test fixtures passed through
that same mapping, so the substrate is driven by the real claimer against real Postgres with no
stopgap kind shipping.

Rejected: handlers self-registering by decorator, the runtime registration ADR 0007 rules out.
Rejected: a cooperative stop where a handler polls its signal and returns, since a kind that
forgets to poll ignores `stop`; the claimer cancels the handler task at the tick that reads the
signal, so halting is the engine's job and the handler's last checkpoint survives. Rejected: flat
`service/job_service.py` and `service/fill_gaps_job.py`, which leaves the subject in a filename
prefix and the layer ungrouped once four entities carry kinds.

## Steps

1. Nest the layer — files: `service/extractors/service.py` (moved), its `__init__.py`, `main.py`,
   `tests/test_extractor_service.py`, `tests/test_http.py`, a new
   `docs/decisions/0013-job-kinds-are-handlers.md`, one clause in
   `docs/decisions/0007-layers-own-their-dependencies.md` — proves it: `pytest -q`, green only if
   every importer moved and the layers probe still fails now that a layer has sub-packages. (A1)
2. Domain — files: `domain/job.py`, `domain/job_log.py`, `tests/test_job.py` — proves it:
   `pytest -q tests/test_job.py`, over `JobStatus.is_terminal`, `JobStatus.is_resumable` and
   `JobSignal.settles_at`, so no status rule lives in a caller. (A1, A6, A7, A10)
3. Migration and store — files: `migrations/0002-jobs.sql`, `repo/jobs.py`, `repo/job_logs.py`,
   `tests/conftest.py`, `tests/test_jobs_repo.py`, `tests/test_extractors_repo.py` — proves it:
   `pytest -q tests/test_jobs_repo.py`, applying migrations twice from an empty database, racing
   two claims, expiring a lease by writing `claimed_at` into the past, and rejecting a fenced
   write after the lease moves. (A2, A3, A4, A11)
4. Job service — files: `service/jobs/service.py`, `tests/test_job_service.py` — proves it:
   `pytest -q tests/test_job_service.py`, over spawn writing `extractor_jobs` from the payload's
   `extractor_id`, the signal guards, and resume clearing the claim while keeping the checkpoint.
   (A10, A12)
5. Claimer and seam — files: `service/jobs/handler.py`, `service/jobs/claimer.py`,
   `tests/fake_jobs.py`, `tests/test_claimer.py` — proves it: `pytest -q tests/test_claimer.py`,
   driving a counting kind, a raising kind and an unmapped kind through claim, tick, stop,
   resume-from-checkpoint and kill. (A5, A6, A7, A8, A9)
6. Transport — files: `transport/dto.py`, `transport/http.py`, `tests/test_http_jobs.py`,
   `tests/test_bootstrap.py` — proves it: `pytest -q tests/test_http_jobs.py`, over the five
   routes, both sorts, the filters and the 404/422 mapping. (A10, A11, A12)
7. Composition root — files: `config.py`, `main.py`, `docs/architecture.md`, `CHANGELOG.md`,
   `tests/test_bootstrap.py` — proves it: `pytest -q tests/test_bootstrap.py`, spawning a job
   against `build_app` under its lifespan, waiting for that app's own claimer to settle it
   `done`, then asserting the task is gone after shutdown. (A13, A1)

## Risks & open

- Two job facts are written down nowhere: an eval's "result metadata" (`docs/architecture.md:41`)
  is no column at `:43`, and `job_logs.level` has no values. Taken: aggregates land in `progress`
  at the terminal write; `JobLogLevel` is `info`, `warning`, `error`, and the claimer writes the
  lifecycle trail so a job has logs before any kind does. Reversible by a column and a member.
- The tick and the claim TTL are numbered nowhere. Taken: `JOB_TICK_SECONDS` 2 and
  `JOB_CLAIM_TTL_SECONDS` 30 as configuration, so tests run them in milliseconds; step 7 adds both
  to `docs/architecture.md:86`. A TTL under the tick reads as a live worker losing its lease.
- Stopping cancels the handler task, so one that swallows cancellation never returns. Taken: the
  claimer waits a bounded time, then settles the row and logs that it did.
- Sorting by duration reads `now()` for a running job, so its position moves between pages and a
  walk over running rows can repeat or skip one. `sort` is a declared optional defaulting to
  `created_at`, ascending; reversible by ordering on `finished_at` and by an `order` parameter.
- No route spawns a job until fill-gaps lands, so `spawn` is exercised by tests and step 7's
  end-to-end path only; reversible by the generic spawn route, at the cost of an ADR.
- `AGENTS.md` says "keep the tree flat" where ADR 0007 says flat and one entity per file. Taken:
  ADR 0007 is the precise statement and the one ADR 0013 amends; two levels grouped by subject
  leaves the `AGENTS.md` line true, reversible with one clause there.
