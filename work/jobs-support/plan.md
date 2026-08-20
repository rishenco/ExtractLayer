# Jobs

Status: Draft

## TL;DR

- Afterwards: asynchronous work has a substrate — `jobs`, `job_logs`, `extractor_jobs`, a service that
  spawns and reads them, a claimer that works one under a fenced lease, and five REST routes.
- Decided: a ticker beside the handler renews the lease and fails closed — a renewal that touches no row,
  raises, or arrives late cancels the handler, and the claimer then writes nothing more to that row;
  shutdown settles nothing, so a restart leaves jobs `running` for the next process to claim past the
  TTL; the claimer holds its own pool, so request traffic cannot starve a lease; a handler records
  progress, metadata, checkpoints and logs through a context and returns nothing, so a stopped run keeps
  its partial aggregates; the claim filters to the kinds a process registers, so an old process leaves a
  new kind alone; `stopped` and `error` resume from their checkpoint, `done` and `killed` refuse; the
  product registers no handler, `tests/` registers the ones that prove the machinery.
- Shape: domain + `job.py`, `job_log.py`; service + `jobs.py`, `job_context.py`, `job_claimer.py`; repo
  + `jobs.py` over three tables; transport + `jobs.py`; main + a claimer pool and its task; config + the
  lease TTL and the tick interval.

## Problem / Intent

Nothing asynchronous can run. `docs/architecture.md:43` and ADR 0011 make a job the one shape of
asynchronous work — gap-filling, evals, training, agentic drafting, maintenance — and no table, service
or route exists for one. Every capability after `serve` in the build order at `docs/vision.md:42` is a
job kind, so all of them wait on a substrate none can afford to build for itself.

Afterwards: a job service inserts a job, claims unleased ones of the kinds it knows under a fenced
lease, renews and ticks them independently of the work, takes `stop`, `kill` and `resume`, and settles
every job at a terminal status; the app runs a claimer beside its API, and the five routes
`docs/architecture.md:54` and `:58` name serve it.

Objections:
- A substrate whose only handler is a test double is an abstraction with no real caller, which
  `AGENTS.md:41` rejects; the alternative proposed was gap-filling as its first real kind, on top of the
  approved `work/datasets-models-and-serve/plan.md`. Decided against: jobs land on today's tree ahead of
  datasets and models, and real kinds are separate changes. The cost is carried here: no job exists in
  production until a kind lands.
- `docs/architecture.md:43` promises kind-specific metadata and lists no column for it. Decided: the
  column is added and that list amended — a contract fixed here needs a result channel.

## Criteria

- [ ] C1 Migration `0002` builds `jobs`, `job_logs` and `extractor_jobs` from an empty database, is safe
      to re-run, and `jobs` carries exactly the columns `docs/architecture.md` lists.
- [ ] C2 A spawned job is `running` with its payload, no claim and no `finished_at`; a payload carrying
      `extractor_id` writes an `extractor_jobs` row in the same transaction, one without writes none.
- [ ] C3 Claiming is exclusive: claimers run concurrently against a seeded set, each job is claimed
      exactly once, none twice and none skipped.
- [ ] C4 A lease older than the TTL is claimable again with no transition written and a fresh
      `claim_id`, and a fenced write carrying the superseded `claim_id` changes no row.
- [ ] C5 The claim is filtered to the kinds a claimer registers: a job of an unregistered kind is left
      unclaimed and stays `running`, and a claimer with no kinds claims nothing.
- [ ] C6 The tick renews the lease independently of the handler: a handler that awaits past the TTL
      without touching its context keeps its claim, and a second claimer finds nothing.
- [ ] C7 The tick fails closed: a renewal that touches no row, one that raises, and one arriving later
      than the TTL each end the handler, after which the claimer writes nothing more to that row.
- [ ] C8 `stop` settles the job `stopped` with its checkpoint kept, `kill` settles it `killed`, both end
      a running handler, and every settlement is fenced on the claim and clears `signal`.
- [ ] C9 A signal on an unclaimed `running` job settles at the claim: the handler is never entered.
- [ ] C10 `resume` returns a `stopped` or `error` job to `running` with claim, signal, error and
      `finished_at` cleared and the checkpoint kept, and the next claim hands that checkpoint to the
      handler; `resume` on `running`, `done` or `killed`, and `stop` or `kill` on a settled job, are 400.
- [ ] C11 A handler that returns settles the job `done` with `finished_at` set and the metadata it
      recorded stored; one that recorded none stores none rather than an empty value.
- [ ] C12 The context is the handler's whole surface: a handler reports progress, records metadata,
      writes a checkpoint and appends a log through it, and the job and log routes return them in order.
- [ ] C13 A raising handler settles the job `error` with its message stored; the claimer goes on claiming.
- [ ] C14 `GET /jobs` and `GET /extractors/{id}/jobs` are cursor-paginated and filterable by kind and
      status, the second scoped to that extractor; `POST /jobs/{id}/signal` rejects an unknown signal by
      name and defaults no field.
- [ ] C15 Shutdown settles nothing: the lifespan starts the claimer and cancels it, a job claimed then is
      left `running` under its lease for another process to take past the TTL, the pools close after the
      claimer stops, and `GET /openapi.json` still serves.

## Not doing

- The real kinds — `fill-gaps`, `train`, `eval` — and the `POST /extractors/{id}/jobs/*` routes that
  spawn them. No route creates a job, so `GET /jobs` is empty in production until a kind lands. The
  metric engine, `eval_scores` and the `/evals` read view go with them.
- Datasets, models, rows and `serve`, which `work/datasets-models-and-serve/plan.md` holds, including
  its move of `repo/` to `repo/pg/`. This change leaves that tree alone.
- Sorting `GET /extractors/{id}/jobs` by duration and reverse paging of `GET /jobs/{id}/logs`: both need
  a cursor over a second column, and the created-at order of the id cursor is what ships.
- Retention or eviction of `jobs` and `job_logs`; history is kept until a policy is chosen. A worker
  entrypoint of its own — scaling is more app processes against one database — job priorities, retries,
  backoff and dependencies between jobs; the OpenRouter client, MCP, auth and the UI.

## Research

- `docs/architecture.md:43` fixes the columns of all three tables and the statuses, and names no column
  for the "kind-specific metadata" the same line promises; `:41` puts an eval's aggregates in that
  metadata and keeps them for error and killed runs. `:54` and `:58` fix the five routes, `:54`
  promising a duration sort no column carries; `:86` names no lease TTL or tick and makes more processes
  the scaling story.
- `docs/decisions/0011-jobs-claimed-from-the-database.md:13` fixes claiming as `FOR UPDATE SKIP LOCKED`
  with every worker write fenced on `claim_id`, and that a dead worker's job returns to the queue with
  no transition written for it; `:15` the ~2s tick; `:17` that a claimer reads `signal` before it starts
  work. `docs/decisions/0012-async-python-psycopg.md:13` puts the claimer on the API event loop and
  `:21` warns that a synchronous call in a coroutine stalls it.
- `extractlayer/transport/http.py:78` `create_app(extractors, lifespan=None)` already takes a lifespan;
  `extractlayer/main.py:21` defines the only one, opening the pool and closing it in a `finally`;
  `extractlayer/repo/postgres.py:28` opens that pool with no sizing. No `asyncio.create_task`, `sleep`
  or `gather` exists anywhere in the repo.
- `extractlayer/repo/extractors.py:16` a `COLUMNS` constant reused in every statement, `:20` a frozen
  `*Row` with `as_*()`, `:53` `class_row`, `:57` `Jsonb(...)`, `:80` the `WHERE id > %s ORDER BY id
  LIMIT %s` cursor; every method is one statement in its own `pool.connection()`, and no multi-statement
  transaction, index or `uuid` column exists in the tree. `extractlayer/service/extractors.py:13`
  declares a module-private `_ExtractorRepo(Protocol)` above its consumer; `pyproject.toml:87` names
  packages, so a new module inside a layer needs no edit.
- `tests/conftest.py:26` makes a throwaway database per test, `:39` yields a repo over an open pool, and
  `pyproject.toml:80` sets `asyncio_mode = "auto"`. Four assertions break on contact:
  `tests/test_extractors_repo.py:47` pins exactly one applied migration, `:29` a table's column list
  which C1 copies, `tests/test_bootstrap.py:25` the exact OpenAPI path list, and `tests/test_http.py:136`
  that no transport field is defaulted. `scripts/gates/10-comments.sh:21` allows no `--` line in `.sql`
  and `scripts/gates/45-doc-links.sh:16` no `file.ext:NN` citation in any `.md` outside `work/`;
  `docs/decisions/template.md:1` fixes the ADR sections, 0012 being the highest number on disk.

## Approach

The change is a vertical slice for one entity, as change 1 was, with the claimer the one piece that has
no precedent to copy. `domain` holds the Job, its statuses and which signal each accepts — invariants of
the entity, so `JobStatus.is_terminal` and the refusal of a `resume` on a `killed` job live on the type,
and the migration's CHECK constraints hold the same sets in storage. `service` splits three ways because
the responsibilities are three: `JobService` answers API calls, `JobContext` is the handler's whole
surface, and `JobClaimer` claims a row, ticks it and settles it. Each declares the repo protocol it
consumes and one `PostgresJobRepo` satisfies them structurally; `repo/jobs.py` owns all three tables,
because ADR 0011 gives the job service sole write access and a `JobLog` is a job's trail rather than an
entity with use cases of its own.

The claimer's shape is the decision worth an ADR, and it turns on failing closed. A ticker task runs
beside the handler task, renewing `claimed_at`, flushing the latest progress and metadata and reading
`signal`, all fenced on its own `claim_id`, from a pool the claimer holds alone so request traffic
cannot starve a lease. Losing the lease is four events, not one: the fenced write touches no row, the
write raises, the tick arrives later than the TTL because a handler blocked the loop, or the process is
shutting down. The first three end the handler and leave the row to whoever holds it now; shutdown ends
it and writes nothing at all, so a restart leaves the job `running` under a lease that expires on its
own — the path ADR 0011 already gives a dead worker. A handler therefore never settles its own row and
cannot forget a `stop`, and it records metadata as it goes rather than returning it, so a run stopped
halfway keeps the aggregates it reached.

Rejected: ticks driven by the handler calling into its context, which loses the lease inside any call
longer than the TTL and makes a forgetful handler unstoppable. Rejected: the handler's return value as
the metadata channel, which leaves a stopped, killed or resumed run with nothing, against
`docs/architecture.md:41`. Rejected: settling an unregistered kind `error`, which makes a rolling deploy
destroy the jobs the new processes spawn. Rejected: a `JobKind` enum in `domain`, making every new kind
a change to the substrate ADR 0006 says it must not be.

## Steps

1. Domain — files: `extractlayer/domain/job.py`, `domain/job_log.py`, `tests/test_job.py` — proves it:
   `pytest -q tests/test_job.py`, which drives every status against every signal. (C10)
2. Store — files: `extractlayer/migrations/0002-jobs.sql`, `extractlayer/repo/jobs.py`,
   `docs/architecture.md`, `tests/test_jobs_repo.py`, `tests/test_extractors_repo.py`, `CHANGELOG.md` —
   the migration keys `extractor_jobs` by `job_id`, constrains `status` and `signal` to their domain
   sets, and indexes the claim predicate and `job_logs` by job — proves it:
   `pytest -q tests/test_jobs_repo.py tests/test_extractors_repo.py`, applying both migrations twice
   from empty, pinning the column list, racing concurrent claims, expiring a lease by writing
   `claimed_at` into the past, and replaying a superseded `claim_id`. (C1, C2, C3, C4, C5)
3. Job service — files: `extractlayer/service/jobs.py`, `tests/test_jobs_service.py` — proves it:
   `pytest -q tests/test_jobs_service.py`. (C2, C10)
4. Context and claimer — files: `extractlayer/service/job_context.py`, `service/job_claimer.py`,
   `extractlayer/config.py`, `docs/decisions/0013-job-handlers-run-under-a-leased-context.md`,
   `docs/architecture.md`, `tests/test_job_claimer.py` — proves it: `pytest -q tests/test_job_claimer.py`,
   with handlers that sleep past the TTL, block the loop, raise, write through the context, and resume
   from a checkpoint. (C6, C7, C8, C9, C11, C12, C13)
5. Transport — files: `extractlayer/transport/jobs.py`, `transport/dto.py`, `transport/http.py`,
   `docs/architecture.md`, whose duration sort drops because no column carries it,
   `tests/test_http_jobs.py`, `tests/test_bootstrap.py` — proves it: `pytest -q tests/test_http_jobs.py
   tests/test_bootstrap.py`, plus `grep -rn duration docs/` returning nothing. (C12, C14)
6. Composition root — files: `extractlayer/main.py`, `extractlayer/repo/postgres.py`,
   `tests/test_bootstrap.py` — `open_pool` takes its sizing and the root opens a second, small pool for
   the claimer — proves it: `pytest -q tests/test_bootstrap.py`, which enters and exits the real
   lifespan with a job claimed and asserts the row is untouched and no task outlives it. (C15)

## Risks & open

- `work/datasets-models-and-serve/plan.md` reserves migration `0002` and ADR `0013`, which this change
  takes as the next free numbers on disk, and its move of `repo/` to `repo/pg/` lists neither
  `repo/jobs.py`, nor this change's `tests/conftest.py` fixture, nor the claimer's `open_pool` import.
  That plan is Approved, so it is not edited here; those four edits fall to its build. Visible as a
  duplicate number and a stranded module then; holes at 0002 and 0013 lose if it is never built.
- Timing tests are the flakiest thing here. The TTL and the tick interval are constructor arguments to
  the claimer, not reads of the environment, so tests drive tenths of a second and assert on stored
  state, never wall-clock. Visible as an intermittent `pytest`; reversible by widening them.
- The claim query, a two-statement transaction, an index and a `uuid` column each have no precedent in
  `repo/`. Step 2 fails at its round-trip test if psycopg does not map `uuid` to `UUID`; the fallback is
  `text`, changing the migration and the architecture's column line together.
- A handler swallowing cancellation delays settlement for as long as it runs, since the claimer awaits
  the cancelled task rather than abandoning it. Visible as a job `running` past its signal.
- `job_logs` inserts are neither fenced nor buffered: batching loses the lines explaining the crash they
  exist for, and fencing each means a join per line. A zombie can append to a job it no longer owns.
- `extractor_jobs.extractor_id` carries a foreign key and `spawn` does not check the extractor first:
  its only callers are services that already loaded it, and a named error for a path no route reaches is
  scope this change does not have. A bad id surfaces as a driver error, not a 400.
- Assumptions taken: one claimer works one job at a time and concurrency is more processes, as
  `docs/architecture.md:86` says, and the idle poll between empty claims is the tick interval rather than
  a third knob. Reversible by a bounded task group and a third knob.
- Every proof above needs the workspace installed, a Postgres on 5432, and `pytest`, `mypy` and `ruff`
  resolving to the interpreter holding the workspace's dependencies, not a tool shim earlier on `PATH`.
