# Datasets, models and serve

Status: Draft

## Problem / Intent

An extractor is a name, a source-column list and a schema with nothing to run and nothing to run
it on. No table holds specimen rows, no model exists, and no route turns a source row into a
derived one, so the loop the product is built around — observe an extraction, test it, make it
cheaper — has neither data nor an execution seam. `specimen_model_id` and `serving_model_id` are
absent because they point at a table that does not exist.

Afterwards: an extractor owns datasets of rows and models; `POST /extractors/{id}/serve` takes one
`source_values` row and returns its derived row through the serving model; and a `dummy` model kind
executes deterministically, so the serve path is covered by `make check` with no network call.
Second of four changes; jobs and MCP follow.

Objections: `docs/architecture.md` calls models "immutable and deletable" and lists
`DELETE /models/{id}`. Decided against it — a model is archived, never deleted, and a model bound
to a model role cannot be archived, because eval history and `known_datasets` name models by id and
a hard delete makes that history unreadable. ADR 0013 records it; the architecture is amended.
Decided: `POST /rows` rejects the whole batch when any row fails validation, because a half-applied
batch has no way to report which half landed; best-effort per-row rejection is a property of the
file import this change leaves alone.

## Criteria

- [ ] B1 A row is validated against its extractor: a source value that is missing, not a string or
      not a source column is rejected by name, an unknown derived column likewise, a derived column
      may be null, and a missing derived column normalizes to null.
- [ ] B2 Migration 0002 builds `models`, `datasets`, `dataset_rows` and the two extractor role
      columns from an empty database and is safe to re-run.
- [ ] B3 Model create and read round-trip over REST; no update route exists.
- [ ] B4 `POST /models/{id}/archive` archives; archiving a model bound to a role is a named 400, an
      archived model still reads through `GET /models/{id}`, and setting one as a role is rejected.
- [ ] B5 Dataset create, list and update round-trip, cursor-paginated; `extractor_id` is
      create-only; `GET /datasets/{id}/rows` is cursor-paginated.
- [ ] B6 `POST /rows` inserts rows with no id, updates rows with one and deletes rows carrying
      `dead: true`, across more than one dataset per call; one invalid row makes it a 422 whose
      `details` names the failing row by index, and no row in that batch lands.
- [ ] B7 `POST /extractors/{id}/serve` returns a derived row through the serving model, falls back
      to the specimen when the serving role is unset, and is a named 400 when neither is set.
- [ ] B8 Execution is a seam: the service selects an executor by the specification's `kind`, an
      unknown kind is a named error at model creation, the `dummy` kind runs with no network, and a
      model returning a row the schema rejects is a 502.
- [ ] B9 Both roles are set through `PUT /extractors/{id}`; a role naming another extractor's model
      is rejected by name.
- [ ] B10 `GET /extractors/{id}` carries its datasets' ids, names and descriptions, and its
      non-archived models' ids, kinds and known datasets.
- [ ] B11 A schema edit rewrites stored rows in the same write: an added column reads null on older
      rows, a removed column's values are gone.

## Not doing

- Jobs, `job_logs`, `extractor_jobs`, the claimer, gap-filling, training and evals — change 3, so
  nothing here writes a row with `source: ai` and `known_datasets` is written only at model
  creation. MCP — change 4. The metric engine and `eval_scores`.
- `POST /datasets/{id}/import`, which adds multipart handling and a format decision wanting its own
  ADR while `POST /rows` already lands rows.
- The OpenRouter client and every real LLM call, so no model spends money and `x-el` stripping
  still belongs to the client that makes the call. Persisting what `serve` returns: no table holds
  historical extractions.
- `DELETE /datasets/{id}`, which the API list does not carry; server-side model forking, a
  client-side `GET` plus `POST`; filtering `GET /datasets` by extractor; auth; the UI.

## Research

- Row validation does not exist. `domain/schema.py:72` holds `parse`, `edited` and `columns` only,
  and `Draft202012Validator` appears once, at `:90`, as `check_schema`; nothing wraps a column
  `anyOf` null, drops `required` or rejects an unknown column. `domain/errors.py:16`
  `ValidationError(details)` is a flat path→message map, and `transport/errors.py:15` maps error
  type to status by first isinstance match, default 400.
- `repo/extractors.py:16` a `COLUMNS` constant, `class_row(ExtractorRow)`, `Jsonb(...)`,
  `RETURNING`, and `" WHERE id > %s"` with `ORDER BY id LIMIT %s` for the cursor (`:74`); no
  `int[]` precedent. `transport/dto.py:11` a `Payload` base with `extra="forbid"`, views with
  `.of(entity)` (`:37`).
- `pyproject.toml:87` the import-linter contract enumerates packages, not modules, so new modules
  inside a layer need no edit. `mypy` is strict tree-wide (`:71`). `tests/conftest.py:26` makes a
  throwaway database per test; `tests/test_http.py:34` wires the real service over the real repo.
- Three assertions break on contact: `test_bootstrap.py:25` pins the exact OpenAPI path list,
  `test_extractors_repo.py:31` the exact `extractors` column list, and `:46` that exactly one
  migration is applied. `10-comments.sh:8` allows no `--` comment in `.sql`, and `20-budgets.sh:8`
  caps `.sql` at 400 lines and `docs/` at 200; ADRs are exempt and 0012 is the highest number.

## Approach

The change repeats change 1's vertical slice for three entities at once, because they only prove
themselves together: a row is meaningless without an extractor to validate it against, and `serve`
is meaningless without a model to run. Row validation lands in `domain` — it is an invariant of the
extractor, not a use case — so `Extractor.validated_row` splits a flat `values` map by
`source_columns` and hands the rest to `ExtractorSchema.derived_values`. The executor is a
`Protocol` the extractor service declares and a mapping of `kind` to implementation the composition
root passes, so a later OpenRouter executor is a second entry rather than an edit. `dummy` is not a
stopgap: a model answering null for every column is the constant baseline an eval measures against,
and it keeps `make check` off the network permanently.

Serve is a method on `ExtractorService`, not a service of its own: it is an extractor use case at
an extractor route, and a `ServeService` would own no entity. Rejected: the schema-edit row rewrite
as a second repo call — two calls mean two transactions and a schema that outruns its rows, so the
service computes the added and removed columns from the domain and the extractor repo applies them
beside the schema write in one transaction. Rejected: archiving as `DELETE /models/{id}` with
soft-delete semantics, since a `DELETE` leaving the row readable lies on the wire. Rejected: a
per-schema cache of the nullable validator, which is a cache with no bound.

## Steps

1. Domain — files: `extractlayer/domain/schema.py`, `domain/extractor.py`, `domain/model.py`,
   `domain/dataset.py`, `domain/dataset_row.py`, `domain/errors.py`, `tests/test_row_values.py`,
   `CHANGELOG.md` — proves it: `pytest -q tests/test_row_values.py tests/test_schema.py`. (B1, B8)
2. ADR and architecture — files: `docs/decisions/0013-models-are-archived.md`,
   `docs/architecture.md` — proves it: `make check` over the edit, plus
   `grep -rn 'DELETE /models' docs/` returning nothing. (B4)
3. Store — files: `extractlayer/migrations/0002-datasets-models.sql`, `repo/models.py`,
   `repo/datasets.py`, `repo/rows.py`, `repo/extractors.py`, `tests/test_extractors_repo.py`,
   `tests/test_models_repo.py`, `tests/test_datasets_repo.py` — proves it:
   `pytest -q tests/test_extractors_repo.py tests/test_models_repo.py tests/test_datasets_repo.py`,
   which applies both migrations twice from empty and pages a seeded set. (B2, B5, B6, B11)
4. Services and the executor seam — files: `extractlayer/service/models.py`,
   `service/datasets.py`, `service/extractors.py`, `repo/executors.py`,
   `tests/test_models_service.py`, `tests/test_datasets_service.py`, `tests/test_serve.py` —
   proves it: `pytest -q tests/test_models_service.py tests/test_datasets_service.py
   tests/test_serve.py`. (B4, B7, B8, B9, B10, B11)
5. Transport — files: `extractlayer/transport/dto.py`, `transport/datasets.py`,
   `transport/models.py`, `transport/http.py`, `extractlayer/main.py`, `tests/test_http.py`,
   `tests/test_http_datasets.py`, `tests/test_http_models.py`, `tests/test_bootstrap.py` — proves
   it: `pytest -q tests/test_http.py tests/test_http_datasets.py tests/test_http_models.py
   tests/test_bootstrap.py`. (B3, B4, B5, B6, B7, B9, B10)

## Risks & open

- `models` and `extractors` reference each other, so 0002 creates `models` first and then alters
  `extractors` to add both role columns. Visible as a failing `yoyo apply` in step 3.
- Archiving reads the extractor's roles then writes the model, which two calls cannot make atomic.
  Taken: one conditional `UPDATE ... WHERE NOT EXISTS (the role query)`, re-reading the row to tell
  "not found" from "in use" so the error stays named. Reversible to read-then-write.
- `dead` is required on every row of `POST /rows`, because `tests/test_http.py:133` pins that
  nothing is defaulted. Noisy for the common case; reversible by making it `bool | None`.
- Every proof above assumes the workspace installed and a Postgres answering on 5432, and that
  `pytest` and `mypy` resolve to the interpreter holding the workspace's dependencies rather than
  an isolated tool shim. A step whose command cannot be executed is claimed as nothing.
- An extractor's deletion cascades to its datasets, rows and models, and a dataset's to its rows,
  because an extractor owns them and no route deletes them separately. Visible as a foreign key
  violation on `DELETE /extractors/{id}`; reversible in the migration before production rows exist.
- `GET /datasets` carries no extractor filter, since `GET /extractors/{id}` embeds them already.
- The nullable validator is rebuilt per row validated; reversible by building it once per request.
- `known_datasets` is `int[]` with no precedent in `repo/`. Step 3 fails at the round-trip test if
  psycopg does not map it to `list[int]`; the fallback is `jsonb`, changing the migration and the
  architecture's table line together.
