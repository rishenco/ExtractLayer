## C1
Claim: `make check` passes — every gate in `scripts/gates/` reports ok, including `ruff check .`, `mypy .` and `pytest -q` through `60-workspaces`.
Evidence: `make check` prints `all gates pass` and exits 0.
Verify: make check
Verdict: SUPPORTED

## C2
Claim: `lint-imports` passes on the tree as it stands, and fails naming the contract and the chain when a `service` module imports `repo` or a `domain` module imports `config`.
Evidence: `tests/test_boundaries.py:44` runs it on the real tree; `:50` writes `extractlayer/service/probe.py` importing `extractlayer.repo` and `:58` writes `extractlayer/domain/probe.py` importing `extractlayer.config`, each asserting a non-zero exit and the output naming "Dependencies point inward" and the offending chain.
Verify: pytest -q tests/test_boundaries.py
Verdict: SUPPORTED

## C3
Claim: `ExtractorSchema.parse` rejects a non-object schema, an object with no properties and an unknown `x-el` key, each naming the path that failed, and accepts a draft 2020-12 object carrying `x-el` metric config on a column and on an array's `items`.
Evidence: `tests/test_schema.py:22` accepts the object carrying both metric positions; `:29`, `:43` and `:49` assert the three rejections and the detail key each carries, and `:59` the same key on an array's `items`.
Verify: pytest -q tests/test_schema.py
Verdict: SUPPORTED

## C4
Claim: an extractor round-trips over REST against Postgres: `POST` then `GET /{id}` returns what was stored, `PUT` replaces name, description and schema, and `DELETE` makes the next `GET` a 404.
Evidence: `tests/test_http.py:43`, `:56` and `:70` drive the three paths through an ASGI client over `PostgresExtractorRepo`.
Verify: pytest -q tests/test_http.py tests/test_extractors_repo.py
Verdict: SUPPORTED

## C5
Claim: `GET /extractors` walks a seeded set of 7 once under `after_id` plus `limit`, repeating no row and skipping none.
Evidence: `tests/test_http.py:77` seeds 7, pages by 3, and asserts the walked ids equal the seeded ids in order and carry no duplicate.
Verify: pytest -q tests/test_http.py -k cursor
Verdict: SUPPORTED

## C6
Claim: a `PUT` carrying `source_columns` is answered 422 naming the field, and the stored extractor is unchanged.
Evidence: `tests/test_http.py:103` asserts the 422 and `source_columns` in `details`, then re-reads the extractor and asserts its name and source columns are as created; `extractlayer/transport/dto.py:12` forbids extra fields and `extractlayer/transport/dto.py:22` declares `ExtractorUpdate` without one.
Verify: pytest -q tests/test_http.py -k source_columns
Verdict: SUPPORTED

## C7
Claim: a write missing a required field is answered 422 whose `details` carries one message per missing field, and no missing field is filled with a default.
Evidence: `tests/test_http.py:123` deletes each of the four create fields in turn and asserts `details[<field>] == "Field required"`; `tests/test_http.py:133` posts only `name` and asserts `details` lists exactly the other three; `tests/test_http.py:97` asserts a listing with no `limit` is a 422 naming `limit`.
Verify: pytest -q tests/test_http.py -k "missing or defaulted or limit"
Verdict: SUPPORTED

## C8
Claim: a `NotFoundError` becomes a 404 on `GET`, `PUT` and `DELETE` alike, and a domain `ValidationError` becomes a 422 carrying the domain's own `details`, decided by the error's type in one handler rather than by any route.
Evidence: `tests/test_http.py:139` asserts 404 on all three routes; `tests/test_http.py:150` asserts the 422 carries `schema.properties`; `extractlayer/transport/errors.py:50` registers the one handler for `DomainError`, and the five routes at `extractlayer/transport/http.py:44`, `:51`, `:59`, `:63` and `:70` catch nothing.
Verify: pytest -q tests/test_http.py -k "404 or validation_error"
Verdict: SUPPORTED

## C9
Claim: a schema edit changing a kept column's type is refused at the domain, the service and over REST — for a flat column, for an array's element type, for an object column's nested property and for an enum's value type — while adding and removing columns, widening an enum within one value type, and editing a description or metric config all succeed.
Evidence: at the domain `tests/test_schema.py:81` (flat), `:98` (array element), `:112` (nested property) and `:130` (enum value type) refuse, while `:140`, `:152`, `:172` and `:189` succeed; at the service `tests/test_extractor_service.py:59` refuses with the stored schema asserted unchanged and `:70` succeeds; over REST `tests/test_http.py:158` and `:173` refuse.
Verify: pytest -q tests/test_schema.py tests/test_extractor_service.py tests/test_http.py
Verdict: SUPPORTED

## C10
Claim: the migrations build `extractlayer.extractors` with its seven columns from an empty database, and applying them a second time leaves one recorded migration and no error.
Evidence: `tests/test_extractors_repo.py:13` applies them to a database created for the test and asserts one relation in the `extractlayer` schema named `extractors` and its seven column names; `tests/test_extractors_repo.py:38` applies them twice and asserts `_yoyo_migration` holds one row.
Verify: pytest -q tests/test_extractors_repo.py -k migrations
Verdict: SUPPORTED

## C11
Claim: `docker compose config` resolves an `app` service built from the repository root and a `db` service on `postgres:16`, with `app` waiting on `db` being healthy and publishing 8420.
Evidence: `docker-compose.yml:2` declares the app, `:9` its published port, `:12` its `service_healthy` condition on `db`, `:15` the `postgres:16` image and `:25` the database health check.
Verify: docker compose config
Verdict: SUPPORTED

## C12
Claim: `build_app` applies the migration to an empty database, opens the pool under the app's lifespan and serves `GET /openapi.json` as a document titled ExtractLayer carrying both extractor paths, and a `POST` then `GET` round-trips through it.
Evidence: `tests/test_bootstrap.py:14` builds the app from a `Config` naming a database created empty for the test, enters the lifespan, and asserts the document's title, its paths, a 201 and the re-read body.
Verify: pytest -q tests/test_bootstrap.py
Verdict: SUPPORTED

## C13
Claim: yoyo applies these migrations over psycopg 3 through its `postgresql+psycopg` backend, so no second database driver is installed.
Evidence: `extractlayer/repo/postgres.py:12` names the scheme; `pyproject.toml:9` declares `psycopg[binary,pool]` and no psycopg2.
Verify: python3 -c "from importlib.metadata import entry_points; print([e.name for e in entry_points().select(group='yoyo.backends') if 'psycopg' in e.name])" && ! grep -q psycopg2 pyproject.toml && echo "no psycopg2 declared"
Verdict: SUPPORTED
