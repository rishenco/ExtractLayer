# Extractors end to end

Status: Approved

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

- [x] A1 (C1) `make check` passes with the workspace present: every gate, plus `ruff`, `mypy` and
      `pytest`.
- [x] A2 (C2) The layer map is enforced, not described: a `service` module importing `repo` makes
      `pytest` fail, and the same test passes on the real tree.
- [x] A3 (C3) Schema validation holds the domain rule: a non-object schema, an object with no
      properties, and an unknown `x-el` key are each rejected by name; a draft 2020-12 object
      carrying `x-el` metric config on a column and on an array's `items` is accepted.
- [x] A4 (C4) Extractor CRUD round-trips over REST against Postgres: `POST` then `GET /{id}` returns
      what was stored, `PUT` updates name, description and schema, `DELETE` makes the next
      `GET` a 404.
- [x] A5 (C5) `GET /extractors` is cursor-paginated: `after_id` plus `limit` walks a seeded set once,
      no row repeated, none skipped.
- [x] A6 (C6) `source_columns` is create-only: a `PUT` carrying it is rejected, not ignored.
- [x] A7 (C7) No transport field is defaulted: a write missing a required field is a 422 carrying
      per-field messages in `details`.
- [x] A8 (C8) Domain errors map to codes at the transport edge from the error type, not per route:
      not found to 404, validation to 422.
- [x] A9 (C9) A schema edit that changes a column's type is refused; adding and removing columns
      succeeds.
- [x] A10 (C10) Migrations build the schema from an empty database and are safe to re-run.
- [ ] A11 `docker compose up` reaches a serving app: `GET /openapi.json` returns the document.
      Not ticked: C11 settles the compose file and C12 the serving app, and no Docker daemon
      runs here to settle the two together.

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
  any manifest exists; it checks presence and never invokes `vale`.
  `scripts/install-workspaces.sh:14` runs `pip install -e '.[dev]'` and fails with no `dev`
  extra. `.github/workflows/ci.yml:20` sets up Python 3.11 and declares no services.
  `scripts/gates/40-changelog.sh:23` wants `CHANGELOG.md` in the changed set once code changes.
- `importlinter` is not installed here; `ruff`, `mypy` and `pytest` are. `.gitignore:2` ignores
  every Python cache and `.venv/`. No `pyproject.toml`, `.py`, `.sql` or `.vale.ini` exists.

## Approach

The change lands as a vertical slice through all four layers of `docs/architecture.md` for one
entity, so the layer map is proven by a running path rather than by a diagram. `domain` holds
the Extractor and the schema's structure; `service` holds the use cases and declares
`ExtractorRepo` as a `Protocol`; `repo` satisfies that protocol against Postgres; `transport`
maps HTTP to `ExtractorService`, another `Protocol`, and maps domain error types to status
codes. Each protocol is declared in the file that consumes it, not a `dependencies` module: it
has one caller, and an abstraction earns a module of its own at the second. Migrations are not
Python and take part in no layer's import graph, so they sit at `extractlayer/migrations` and
are applied by the composition root, `extractlayer/main.py` — the only module naming a concrete
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
   - Done: root workspace with `[tool.ruff]`, `[tool.mypy]`, `[tool.importlinter]`; `.vale.ini`
     with a real style carrying the `30-slop.sh` and `35-narration.sh` phrases; four layer
     packages; `tests/test_boundaries.py` writes the probe into the real tree under a fixture
     and removes it, so the contract is checked against the tree that ships. Found: the layers
     contract names only the layers that exist, so `extractlayer.main` joins it in step 5.
     Found: `[tool.ruff]` drops `.py` from `10-comments.sh` and `20-budgets.sh`, and ruff has
     no file-length or no-comments rule to replace them — the floor Python loses is real.
2. Domain — files: `extractlayer/domain/errors.py`, `domain/schema.py`, `domain/extractor.py`,
   `tests/test_schema.py` — proves it: `pytest -q tests/test_schema.py`. (A3, A9)
   - Done: `ExtractorSchema.parse` rejects a non-object schema, a non-`object` type, an empty
     `properties`, a schema `Draft202012Validator.check_schema` refuses, and an unknown `x-el`
     key — each naming the path that failed. `ExtractorSchema.edited` re-parses and refuses a
     changed column type. Found: the rules are load-bearing — dropping the empty-properties,
     type-change and unknown-key checks in turn fails 3, 1 and 2 tests. Found: `jsonschema`
     ships no `py.typed`, so `types-jsonschema` joins the `dev` extra.
   - Found in review: that refusal compared only a column's top-level `type`, so an array
     column's element type, an object column's nested property and an enum's value type could
     each be edited freely while the flat equivalent was refused. `_type_shape` now reads the
     column recursively; the three cases fail the suite against the old comparison and pass
     against the new one, at the domain and over REST.
3. Store and migrations — files: `extractlayer/config.py`, `repo/postgres.py`,
   `extractlayer/migrations/0001-extractors.sql`, `repo/extractors.py`, `docker-compose.yml`,
   `.github/workflows/ci.yml`, `docs/decisions/0008-migrations-with-yoyo.md`,
   `docs/decisions/0012-async-python-psycopg.md`, `tests/conftest.py`,
   `tests/test_extractors_repo.py` — proves it:
   `pytest -q tests/test_extractors_repo.py`, which applies migrations twice from an empty
   database and walks a seeded page set. (A10, A4, A5)
   - Done: `0001-extractors.sql` creates the `extractlayer` schema and the table; migrations run
     over yoyo's `postgresql+psycopg` backend, so the risk that it might be absent is closed and
     no `psycopg2-binary` is installed. `tests/conftest.py` creates and drops a database per
     test, so every run starts empty. Found: `yoyo` ships no `py.typed`, and no stub package
     exists, so `pyproject.toml` carries a module override for it rather than a blanket relax.
     Found: `docs/decisions/0009-transport.md` also cites `transport.dependencies`, which the
     plan named only in ADR 0007 and the architecture — it is amended with them in step 4.
4. Service — files: `extractlayer/service/extractors.py`, `docs/architecture.md`,
   `docs/decisions/0007-layers-own-their-dependencies.md`,
   `tests/test_extractor_service.py` — proves it: `pytest -q tests/test_extractor_service.py`.
   (A6, A8, A9)
   - Done: `ExtractorService` declares `ExtractorRepo` as a `Protocol` beside itself, raises
     `NotFoundError` and `ValidationError` only, and takes no `source_columns` on update, so the
     created list survives an edit. Tests drive the real `PostgresExtractorRepo`, since ADR 0010
     puts tests on Postgres rather than a substitute. Amended the layer table, ADR 0007 and
     ADR 0009 off the `dependencies` modules; `grep -rn 'repo/migrations\|\.dependencies' docs/`
     is now empty.
5. Transport — files: `extractlayer/transport/dto.py`, `transport/errors.py`,
   `transport/http.py`, `extractlayer/main.py`, `tests/test_http.py` — proves it:
   `pytest -q tests/test_http.py`. (A4, A5, A6, A7, A8)
   - Done: the wire name is `schema` while the Python field is `document`, because a pydantic
     field named `schema` shadows a `BaseModel` attribute; the OpenAPI document carries `schema`.
     Request bodies forbid extra fields, so a `PUT` carrying `source_columns` is a 422 naming it.
     `limit` is required and `after_id` is a declared optional. Two handlers registered on the
     app map `DomainError` by type and `RequestValidationError` to per-field `details`; no route
     catches anything. `extractlayer.main` joins the layers contract with the module.
6. Bootstrap — files: `Dockerfile`, `docker-compose.yml` — proves it: `docker compose up -d`
   then `curl -fsS localhost:8420/openapi.json`. (A11)
   - Done: `Dockerfile` installs the package and runs `python -m extractlayer.main`; compose adds
     the app beside the database and waits on its health check. Contradicts the plan in what can
     be checked here, not in what was built: no Docker daemon runs in this environment, so
     `docker compose up -d` cannot execute. `docker compose config` resolves both services, and
     the app itself was started against an empty database over `python -m extractlayer.main`,
     which applied the migration, served `GET /openapi.json`, round-tripped a `POST` and `GET`
     and answered 404 for an absent id. Added `tests/test_bootstrap.py`, outside the plan's file
     list and inside its intent, so the composition root serving `GET /openapi.json` from an
     empty database is checked by `make check` rather than observed once. The image build and
     the compose run stay unverified and are claimed as nothing.

## Risks & open

- ADR 0008 and ADR 0007 are amended, not superseded: what each decided still holds, and only a
  path and a module name change. `45-doc-links.sh` does not check `extractlayer/` paths, so the
  check that no citation dangles is `grep -rn 'repo/migrations\|\.dependencies' docs/`.
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
- No Docker daemon runs in the build environment, so A11's `docker compose up -d` was not
  executed. `docker compose config` and a real uvicorn run against an empty database cover the
  app and the compose file separately; the image build and the two containers together are
  unverified until CI or a human runs them.
- `OPENROUTER_API_KEY` is listed as required configuration in `docs/architecture.md`, and no
  model client exists yet. Assumption taken: it is not validated at startup until the client
  that needs it lands, and the architecture document is left unedited because it describes the
  design rather than one change. Reversible in either direction in change 2.
- "A type change is refused" (A9) needed a reading, because a column's content may be non-flat.
  Taken: two versions of a kept column differ in type when their type shape differs, where the
  shape is `type`, `const`, `enum` value types, `items`, `prefixItems` and `properties` read
  recursively. Annotations, constraints and `x-el` are not part of it, so editing a description
  or a metric is not a type change. Reversible by narrowing or widening `_type_shape`.
- `limit` is required and bounded below at 1, with no upper bound: no document sets a maximum
  page size, and a cap is a policy nobody has chosen. Assumption taken: reject a meaningless
  limit, let a large one through, and leave the cap to the change that adds authorization.
  Visible as an unbounded response; reversible by adding `le` to the query parameter.
- `mypy` strictness against FastAPI and pydantic may need per-module overrides. Visible as a
  failing `mypy .`; each override is recorded in `pyproject.toml` rather than a blanket relax.
