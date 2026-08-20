## C1
Claim: A row is validated against its extractor — a missing, non-string or unknown source value and an unknown derived column are each rejected under their own key, a derived column may be null, and a missing derived column normalizes to null.
Evidence: `tests/test_row_values.py` covers each case against `Extractor.validated_row` and `Extractor.validated_source_values`, and a derived column may not shadow a source column, so no name reaches both halves of the split.
Verify: pytest -q tests/test_row_values.py tests/test_extractor_service.py
Verdict:

## C2
Claim: Migration 0002 builds `models`, `datasets`, `dataset_rows` and the two extractor role columns from an empty database and is safe to re-run.
Evidence: `test_migration_0002_builds_every_table_from_an_empty_database` reads `information_schema` after one apply, `test_migration_0002_is_safe_to_re_run` applies twice, and `test_migrations_are_safe_to_re_run` asserts exactly two applied migrations.
Verify: pytest -q tests/test_models_repo.py tests/test_extractors_repo.py
Verdict:

## C3
Claim: A model creates and reads back over REST, and no route updates one.
Evidence: `test_a_model_round_trips_over_rest` posts and re-reads; `test_no_update_route_exists_for_a_model` gets 405 from PUT, PATCH and DELETE on `/models/{id}`.
Verify: pytest -q tests/test_http_models.py
Verdict:

## C4
Claim: `POST /models/{id}/archive` archives, archiving a model a role names is a 400 naming the role, an archived model still reads through `GET /models/{id}`, and setting an archived model as a role is rejected.
Evidence: `test_an_archived_model_still_reads`, `test_archiving_a_model_a_role_names_is_a_named_400` and `test_setting_an_archived_model_as_a_role_is_a_422` in `tests/test_http_models.py`, with the service-level equivalents in `tests/test_models_service.py`.
Verify: pytest -q tests/test_http_models.py tests/test_models_service.py
Verdict:

## C5
Claim: Dataset create, read, list and update round-trip over REST with a cursor, `extractor_id` is create-only, and `GET /datasets/{id}/rows` is cursor-paginated.
Evidence: `test_a_dataset_round_trips_over_rest` reads back through the listing, with `test_a_put_replaces_name_and_description_only`, `test_a_put_carrying_the_extractor_is_rejected`, `test_a_cursor_walks_the_dataset_listing_once` and `test_a_cursor_walks_a_datasets_rows_once` in `tests/test_http_datasets.py`.
Verify: pytest -q tests/test_http_datasets.py
Verdict:

## C6
Claim: `POST /rows` inserts rows with no id, updates rows with one and deletes rows carrying `dead: true` across more than one dataset in a call; one invalid row makes it a 422 whose `details` names the failing row by index and no row of that batch lands.
Evidence: `test_rows_land_update_and_die_in_one_call_across_two_datasets` and `test_one_invalid_row_is_a_422_naming_its_index_and_nothing_lands` in `tests/test_http_datasets.py`, which re-reads the dataset's rows and finds it empty.
Verify: pytest -q tests/test_http_datasets.py tests/test_datasets_service.py
Verdict:

## C7
Claim: `POST /extractors/{id}/serve` returns a derived row through the serving model, falls back to the specimen when the serving role is unset, and is a 400 naming the extractor when neither role is set.
Evidence: `tests/test_serve.py` covers the serving model, the specimen fallback and the preference between them; `test_serving_with_no_model_is_a_named_400` in `tests/test_http.py` pins the wire behaviour.
Verify: pytest -q tests/test_serve.py tests/test_http.py
Verdict:

## C8
Claim: The extractor service selects an executor by the specification's `kind`, an unknown kind is a named error at model creation, the `dummy` kind runs with no network call, and a model returning a row the schema rejects is a 502.
Evidence: `ExtractorService.serve` indexes `self.executors` by `model.kind`; `test_a_specification_naming_an_unknown_kind_is_a_422`, `test_the_dummy_kind_answers_null_for_every_column` and `test_a_model_returning_a_row_the_schema_rejects_is_an_upstream_failure` pass with no network access, and `transport/errors.py` maps `UpstreamModelError` to 502.
Verify: pytest -q tests/test_serve.py tests/test_http_models.py
Verdict:

## C9
Claim: Both model roles are set through `PUT /extractors/{id}`, and a role naming another extractor's model is rejected under that role's own key.
Evidence: `test_a_role_naming_another_extractors_model_is_rejected_by_name` in `tests/test_http_models.py` asserts `details["serving_model_id"] == "names a model of extractor N"`, and `test_archiving_a_model_a_role_names_is_a_named_400` sets a role through the same route.
Verify: pytest -q tests/test_http_models.py tests/test_models_service.py
Verdict:

## C10
Claim: `GET /extractors/{id}` carries its datasets' ids, names and descriptions, and its non-archived models' ids, kinds and known datasets.
Evidence: `test_an_extractor_carries_its_datasets_and_live_models` asserts the models list holds only the unarchived model with its kind and known datasets; `test_an_extractor_carries_its_datasets` asserts the dataset shape.
Verify: pytest -q tests/test_http_models.py tests/test_http_datasets.py
Verdict:

## C11
Claim: A schema edit rewrites the stored rows in the same write — an added column reads null on older rows and a removed column's values are gone — and leaves another extractor's rows untouched.
Evidence: `test_a_schema_edit_rewrites_the_rows_a_dataset_holds` reads back `{"body": "one", "currency": None}` after the edit dropped `total` and added `currency`; `test_a_schema_edit_leaves_another_extractors_rows_alone` pins the scope.
Verify: pytest -q tests/test_http_datasets.py tests/test_datasets_repo.py
Verdict:

## C12
Claim: `make check` passes on this tree.
Evidence: every gate reports ok and the workspace runs ruff, mypy and 157 passing tests.
Verify: make check
Verdict:

## C13
Claim: A derived column may not be named after a source column, at extractor creation and at a schema edit alike.
Evidence: `test_a_schema_column_named_after_a_source_column_is_refused` and `test_a_schema_edit_adding_a_column_named_after_a_source_column_is_refused` in `tests/test_extractor_service.py` assert `details["schema.properties.body"]`.
Verify: pytest -q tests/test_extractor_service.py
Verdict:

## C14
Claim: A batch naming one row id twice is refused under the second row's index and lands nothing, and rows come back in the order the batch named them.
Evidence: `test_a_batch_naming_one_row_twice_names_the_second_index_and_lands_nothing`, `test_a_batch_updating_and_killing_one_row_is_refused_rather_than_silently_dropped` and `test_written_rows_come_back_in_the_order_the_batch_named_them` in `tests/test_datasets_service.py`.
Verify: pytest -q tests/test_datasets_service.py
Verdict:

## C15
Claim: Every route the app serves is named in the REST list of `docs/architecture.md`, and a route that is not fails the build.
Evidence: `test_every_served_route_is_named_in_the_architecture` in `tests/test_bootstrap.py` compares the OpenAPI paths with the routes parsed out of that section, matching path parameters by position.
Verify: pytest -q tests/test_bootstrap.py
Verdict:
