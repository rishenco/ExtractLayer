# Extractors end to end

Status: Draft

## Problem / Intent

The repository holds intent, gates and decision records, and no source. Nothing in
`docs/architecture.md` is executable, so every claim about the design is unfalsifiable —
including whether the layer map, the Postgres conventions and the gate suite can coexist.

Afterwards: a running Python service with four layers wired at a composition root, Postgres
behind numbered migrations, and one entity — Extractor — reachable end to end over REST.
`docker compose up` on a fresh clone reaches a serving app. The one-time cost of the first
Python workspace is paid here, the first of four changes carrying the core logic; the three
after it add capability, not tooling.

Objections: none.

## Criteria

- [ ] A1 `make check` passes with the workspace present: every gate, plus `ruff`, `mypy` and
      `pytest`.
- [ ] A2 The layer map is enforced, not described: a `service` module importing `repo` makes
      `pytest` fail, and the same test passes on the real tree.
- [ ] A3 Schema validation holds the domain rule: a non-object schema, an object with no
      properties, and an unknown `x-el` key are each rejected by name; a draft 2020-12 object
      carrying `x-el` metric config on a column and on an array's `items` is accepted.
- [ ] A4 Extractor CRUD round-trips over REST against Postgres: `POST` then `GET /{id}` returns
      what was stored, `PUT` updates name, description and schema, `DELETE` makes the next
      `GET` a 404.
- [ ] A5 `GET /extractors` is cursor-paginated: `after_id` plus `limit` walks a seeded set once,
      no row repeated, none skipped.
- [ ] A6 `source_columns` is create-only: a `PUT` carrying it is rejected, not ignored.
- [ ] A7 No transport field is defaulted: a write missing a required field is a 422 carrying
      per-field messages in `details`.
- [ ] A8 Domain errors map to codes at the transport edge from the error type, not per route:
      not found to 404, validation to 422.
- [ ] A9 A schema edit that changes a column's type is refused; adding and removing columns
      succeeds.
- [ ] A10 Migrations build the schema from an empty database and are safe to re-run.
- [ ] A11 `docker compose up` reaches a serving app: `GET /openapi.json` returns the document.

## Not doing

- Datasets, dataset rows, models and `POST /extractors/{id}/serve` — change 2, with the dummy
  model executor. `specimen_model_id` and `serving_model_id` arrive in that change's migration:
  they are foreign keys to a table that does not exist yet.
- Jobs, `job_logs`, `extractor_jobs`, the claimer and fake job kinds — change 3.
- MCP — change 4.
- The metric engine and `eval_scores`. `x-el` is validated structurally; no metric kind is
  interpreted.
- The row half of a schema edit. An added column reading null on older rows needs
  `dataset_rows`, so it lands with the table it rewrites.
- Stripping `x-el` before a model call, which belongs with the client that makes the call.
- Auth, the OpenRouter client, the UI.

## Research

- `scripts/lib/files.sh:50` detects a workspace by a root `pyproject.toml`; `50-architecture.sh:27`
  requires the substring `tool.importlinter`, `55-lint-config.sh:22` requires `tool.ruff`,
  `60-workspaces.sh:50` requires `tool.ruff` and `tool.mypy`.
- `scripts/gates/60-workspaces.sh:53` runs `ruff check .`, `mypy .`, `pytest -q` from the
  workspace once any `.py` exists. `pytest` exits 5 when it collects nothing, which the gate
  reads as failure, so the workspace needs a collected test in the same commit.
- `scripts/lib/files.sh:103` treats `[tool.ruff]` as covering the `py` extension only.
  `el_drop_linted` (`files.sh:112`) therefore keeps `.sql` and `.sh` inside `10-comments`,
  `20-budgets` and `30-slop`. `10-comments.sh:20` fails on a `--` line in `.sql` unless it
  matches the directive allowlist (`10-comments.sh:8`), which carries no `depends:` entry.
- `scripts/gates/55-lint-config.sh:39` requires `.vale.ini` or `vale.ini` at the root as soon as
  any manifest exists. It checks presence; the `vale` binary is never invoked.
- `scripts/install-workspaces.sh:14` runs `pip install -e '.[dev]'` and fails when the manifest
  declares no `dev` extra.
- `.github/workflows/ci.yml:20` sets up Python 3.11 and declares no services or containers.
- `scripts/gates/40-changelog.sh:23` requires `CHANGELOG.md` in the changed set once any file
  with a code extension changes.
- `importlinter` is not installed here; `ruff`, `mypy` and `pytest` are. `.gitignore:2` already
  ignores every Python cache directory and `.venv/`. No `pyproject.toml`, `.py`, `.sql`,
  `docker-compose.yml` or `.vale.ini` exists.

## Approach

The change lands as a vertical slice through all four layers of `docs/architecture.md` for one
entity, so the layer map is proven by a running path rather than by a diagram. `domain` holds
the Extractor and the schema's structure; `service` holds the use cases and declares
`ExtractorRepo` as a `Protocol`; `repo` satisfies that protocol against Postgres and owns the
migrations; `transport` maps REST to `ExtractorService`, another `Protocol`, and maps domain
error types to status codes. `extractlayer/main.py` is the only module naming a concrete
adapter. Schema rules sit in `domain` because they are invariants of the entity, not use cases;
metric interpretation stays out because it is a `service` concern with no caller yet.

The runtime is async throughout, on psycopg 3 — recorded as ADR 0012, since no existing decision
names a driver. Rejected: sync with a thread pool, which turns FastAPI, the `mcp` SDK and the
tick loop of ADR 0011 into threadpool offloads and makes the in-process claimer a thread rather
than a task. Rejected: asyncpg, which is async-only, so yoyo would need a second driver.

Rejected for the layers: interfaces in a shared inner module, which makes the layer owning an
interface different from the layer needing it (ADR 0007). Rejected for the entity split:
building all entities at one layer at a time, which leaves no working product until the end.

## Steps

1. Workspace and boundaries — files: `pyproject.toml`, `.vale.ini`, `styles/`,
   `extractlayer/__init__.py`, the four layer packages, `tests/test_boundaries.py`,
   `CHANGELOG.md` — proves it: `pytest -q tests/test_boundaries.py`, which runs `lint-imports`
   on the real tree and again with a probe module importing across a boundary, asserting the
   second run fails and names the contract. (A1, A2)
2. Domain — files: `extractlayer/domain/errors.py`, `domain/schema.py`, `domain/extractor.py`,
   `tests/test_schema.py` — proves it: `pytest -q tests/test_schema.py`. (A3, A9)
3. Store and migrations — files: `extractlayer/config.py`, `repo/postgres.py`,
   `repo/migrations/0001-extractors.sql`, `repo/extractors.py`, `docker-compose.yml`,
   `.github/workflows/ci.yml`, `docs/decisions/0012-async-python-psycopg.md`,
   `tests/conftest.py`, `tests/test_extractors_repo.py` — proves it:
   `pytest -q tests/test_extractors_repo.py`, which applies migrations twice from an empty
   database and walks a seeded page set. (A10, A4, A5)
4. Service — files: `extractlayer/service/dependencies.py`, `service/extractors.py`,
   `tests/test_extractor_service.py` — proves it: `pytest -q tests/test_extractor_service.py`.
   (A6, A8, A9)
5. Transport — files: `extractlayer/transport/dependencies.py`, `transport/dto.py`,
   `transport/errors.py`, `transport/rest.py`, `extractlayer/main.py`, `tests/test_rest.py` —
   proves it: `pytest -q tests/test_rest.py`. (A4, A5, A6, A7, A8)
6. Bootstrap — files: `Dockerfile`, `docker-compose.yml` — proves it: `docker compose up -d`
   then `curl -fsS localhost:8420/openapi.json`. (A11)

## Risks & open

- Migrations are plain SQL with no `-- depends:` line, because that directive is not in the
  allowlist of `10-comments.sh:8` and yoyo orders by filename without it. Visible if a later
  change needs a non-linear history; reversible by adding `depends:` to the allowlist with a
  fixture in `05-selftest.sh`.
- yoyo's psycopg 3 backend name is unverified. Step 3 fails at `yoyo apply` if it is absent;
  the fallback is `psycopg2-binary` as a migrations-only dependency, recorded in ADR 0012.
- `make check` starts requiring a running Postgres, since ADR 0010 forbids a substitute engine
  and ADR 0001 forbids skipping. `docker compose up -d db` is the one command that fixes it.
  Visible as a failing `pytest`, not a silent skip.
- `.vale.ini` satisfies `55-lint-config.sh:39` but no `vale` binary runs in `make check`, so the
  phrase list in `30-slop.sh` stays. ADR 0003 says a config file does not stand in for a check
  that runs; installing Vale in CI and retiring the phrase list is its own change. Assumption
  taken: add the config, keep the phrase list, and leave the debt named here.
- `OPENROUTER_API_KEY` is listed as required configuration in `docs/architecture.md`, and no
  model client exists yet. Assumption taken: it is not validated at startup until the client
  that needs it lands, and the architecture document is left unedited because it describes the
  design rather than one change. Reversible in either direction in change 2.
- `mypy` strictness against FastAPI and pydantic may need per-module overrides. Visible as a
  failing `mypy .`; each override is recorded in `pyproject.toml` rather than a blanket relax.
