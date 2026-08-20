from __future__ import annotations

from typing import Any

import psycopg

from extractlayer.domain.extractor import ExtractorEdit, ModelRoles
from extractlayer.domain.model import ModelKind
from extractlayer.domain.schema import ExtractorSchema
from extractlayer.repo.pg.db import apply_migrations
from extractlayer.repo.pg.extractors import PostgresExtractorRepo
from extractlayer.repo.pg.models import PostgresModelRepo

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
SPECIFICATION: dict[str, Any] = {"kind": "dummy"}
TABLES = ["dataset_rows", "datasets", "extractors", "models"]


def role_edit(
    schema: ExtractorSchema, specimen_model_id: int, serving_model_id: int
) -> ExtractorEdit:
    return ExtractorEdit(
        name="Invoices",
        description="line items",
        schema=schema,
        previous=schema,
        roles=ModelRoles(
            specimen_model_id=specimen_model_id,
            serving_model_id=serving_model_id,
        ),
    )


def test_migration_0002_builds_every_table_from_an_empty_database(empty_database: str) -> None:
    apply_migrations(empty_database)
    with psycopg.connect(empty_database) as connection:
        tables = connection.execute(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema = 'extractlayer' ORDER BY table_name"
        ).fetchall()
        columns = connection.execute(
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_schema = 'extractlayer' AND table_name = 'models'"
            " ORDER BY column_name"
        ).fetchall()
    assert [table[0] for table in tables] == TABLES
    assert [column[0] for column in columns] == [
        "archived_at",
        "created_at",
        "extractor_id",
        "id",
        "known_datasets",
        "specification",
        "updated_at",
    ]


def test_migration_0002_is_safe_to_re_run(empty_database: str) -> None:
    apply_migrations(empty_database)
    apply_migrations(empty_database)
    with psycopg.connect(empty_database) as connection:
        models = connection.execute("SELECT count(*) FROM extractlayer.models").fetchone()
    assert models is not None
    assert models[0] == 0


async def test_a_model_round_trips(
    extractors: PostgresExtractorRepo, models: PostgresModelRepo
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    created = await models.create(extractor.id, SPECIFICATION, [4, 9])
    stored = await models.get(created.id)
    assert stored == created
    assert stored is not None
    assert stored.extractor_id == extractor.id
    assert stored.known_datasets == (4, 9)
    assert stored.kind is ModelKind.DUMMY
    assert stored.is_archived is False


async def test_an_archived_model_still_reads_and_leaves_the_live_listing(
    extractors: PostgresExtractorRepo, models: PostgresModelRepo
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    kept = await models.create(extractor.id, SPECIFICATION, [])
    gone = await models.create(extractor.id, SPECIFICATION, [])

    archived = await models.archive(gone.id)
    assert archived is not None
    assert archived.is_archived is True

    read = await models.get(gone.id)
    assert read is not None
    assert read.archived_at == archived.archived_at
    assert [model.id for model in await models.live_for_extractor(extractor.id)] == [kept.id]


async def test_archiving_twice_keeps_the_first_archive_time(
    extractors: PostgresExtractorRepo, models: PostgresModelRepo
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    created = await models.create(extractor.id, SPECIFICATION, [])
    first = await models.archive(created.id)
    again = await models.archive(created.id)
    assert first is not None
    assert again is not None
    assert again.archived_at == first.archived_at


async def test_a_model_a_role_names_is_not_archived(
    extractors: PostgresExtractorRepo, models: PostgresModelRepo
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    serving = await models.create(extractor.id, SPECIFICATION, [])
    specimen = await models.create(extractor.id, SPECIFICATION, [])
    await extractors.update(
        extractor.id,
        role_edit(extractor.schema, specimen.id, serving.id),
    )

    assert await models.archive(serving.id) is None
    assert await models.archive(specimen.id) is None
    read = await models.get(serving.id)
    assert read is not None
    assert read.is_archived is False


async def test_archiving_a_model_that_does_not_exist_finds_nothing(
    models: PostgresModelRepo,
) -> None:
    assert await models.archive(4321) is None


async def test_deleting_an_extractor_takes_its_models(
    extractors: PostgresExtractorRepo, models: PostgresModelRepo
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    created = await models.create(extractor.id, SPECIFICATION, [])
    assert await extractors.delete(extractor.id) is True
    assert await models.get(created.id) is None
