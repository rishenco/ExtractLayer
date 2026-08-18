# Core spine: transport, service and repo over the job substrate

Status: Draft

## Problem

`docs/architecture.md` describes four layers, the entity tables, a claim-and-lease job
protocol and a REST surface; nothing implements it. No decision there has been tested
against a running system, and everything the vision sequences after the core has nothing
to attach to.

## Intent

A developer reaches a running API from a fresh clone: create an extractor with source
columns and a schema, put rows in a dataset, register a model, call `serve` for derived
values, spawn a gap-filling job and watch its progress, then stop, resume or kill it.
Answers come from a deterministic fake executor, so the path runs with no key and no spend.

## Acceptance criteria

- [ ] `make check` passes with a Python workspace at the repository root: `ruff`, `mypy`,
      `pytest` and the `[tool.importlinter]` contracts all run over `extractlayer/`.
- [ ] A `pytest` test runs those contracts: `transport`, `service` and `repo` never import
      one another, `domain` imports none, only `extractlayer.main` imports `repo`.
- [ ] `pytest` reports zero skipped tests — the suite starts Postgres on a temporary path
      when `DATABASE_URL` is unset, and fails when no database is reachable.
- [ ] yoyo migrations create every table `docs/architecture.md` lists except `eval_scores`,
      with the columns it names; a test applies them to an empty database and asserts them.
- [ ] Job substrate tests prove: concurrent claimers take disjoint rows; a write fenced with
      a stale `claim_id` updates nothing; a row past the claim TTL is claimable with no
      status written for it; `stop` halts at the next tick keeping the checkpoint; `resume`
      returns it to `running`, claim cleared, and restarts from the checkpoint repeating no
      finished step; `kill` settles it terminal.
- [ ] Every REST route in `docs/architecture.md` outside Non-goals answers in tests against
      the running app, mapping errors to the codes that document states, and rejecting an
      omitted required field rather than defaulting it.
- [ ] Every list route pages on `after_id` + `limit`, walked over more than one page with
      each id appearing once.
- [ ] Derived values validate against the extractor's schema: every column nullable, a
      missing column normalizing to null, an unknown column rejected, and `x-el` stripped
      from what reaches the executor — proven by asserting what the fake executor receives.
- [ ] A fill-gaps job fills only rows missing derived columns, marks exactly those rows
      `ai`, writes progress and job logs as it runs, and leaves complete rows untouched.
- [ ] `docker compose up` on a clean checkout answers `GET /extractors` with 200.

## Non-goals

- The metric engine, eval jobs, `eval_scores` and the `/evals` routes — whole in the next
  change rather than as placeholders.
- The MCP facade, mirroring these routes over the same `transport.dependencies` and
  `transport.dto`, next change.
- Training, GEPA, the `train` and `eval` job kinds, agentic drafting, the real OpenRouter
  executor, the embedding provider, `POST /datasets/{id}/import`, authorization, the UI.

## Layer

All four, because this creates them. Entity invariants, schema structure and job status and
signal transitions are `domain`; use cases, the claim-and-tick loop and gap-filling are
`service`, declaring what it consumes in `service.dependencies`; Postgres adapters,
migrations and the fake executor are `repo`, since a fake in `service` could not be swapped
at the composition root when the real one lands; routes and DTOs are `transport`.

## Open questions

- `OPENROUTER_API_KEY` is documented as required. Assumed unread, the composition root
  wiring the fake executor unconditionally; the real adapter makes it required and amends
  `docs/architecture.md` then. Reversible in the composition root.
- What counts as a gap. Assumed: a row whose `values` omits a derived column or holds null
  for it; a row with every derived column filled is skipped. Reversible.
- How tests reach Postgres. Assumed: `pytest` starts a container on a temporary path when
  `DATABASE_URL` is unset and CI installs Docker; reversible to a CI service container.

## Objections

- Dummy metrics were requested. Argued against: the vision sequences the metric engine inside
  the core, AGENTS.md refuses stopgaps, faking costs what writing costs. Decided: real ones next.
- Dummy jobs were requested. Decided the same way: `fill-gaps` ships for real over the fake
  executor, `eval` and `train` not at all — a real executor needs a key and spend CI lacks.
- Argued the requested surface, every entity across both transports, is two changes.
  Decided: REST only here, MCP next.
