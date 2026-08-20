from __future__ import annotations

from typing import Any

import psycopg
import pytest

from extractlayer.domain.extractor import ExtractorEdit, ModelRoles
from extractlayer.domain.schema import ExtractorSchema
from extractlayer.repo.pg import extractors as extractors_repo
from extractlayer.repo.pg.db import apply_migrations
from extractlayer.repo.pg.extractors import PostgresExtractorRepo

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
MIGRATIONS = 2


def edit(
    previous: ExtractorSchema,
    document: dict[str, Any],
    name: str = "Invoices",
    description: str = "line items",
) -> ExtractorEdit:
    return ExtractorEdit(
        name=name,
        description=description,
        schema=ExtractorSchema.parse(document),
        previous=previous,
        roles=ModelRoles(specimen_model_id=None, serving_model_id=None),
    )


def test_migrations_build_the_schema_from_an_empty_database(empty_database: str) -> None:
    apply_migrations(empty_database)
    with psycopg.connect(empty_database) as connection:
        table = connection.execute(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace"
            " WHERE n.nspname = 'extractlayer' AND c.relname = 'extractors' AND c.relkind = 'r'"
        ).fetchone()
        columns = connection.execute(
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_schema = 'extractlayer' AND table_name = 'extractors'"
            " ORDER BY column_name"
        ).fetchall()
    assert table is not None
    assert table[0] == 1
    assert [column[0] for column in columns] == [
        "created_at",
        "description",
        "id",
        "name",
        "schema",
        "serving_model_id",
        "source_columns",
        "specimen_model_id",
        "updated_at",
    ]


def test_migrations_are_safe_to_re_run(empty_database: str) -> None:
    apply_migrations(empty_database)
    apply_migrations(empty_database)
    with psycopg.connect(empty_database) as connection:
        applied = connection.execute("SELECT count(*) FROM _yoyo_migration").fetchone()
        rows = connection.execute("SELECT count(*) FROM extractlayer.extractors").fetchone()
    assert applied is not None
    assert applied[0] == MIGRATIONS
    assert rows is not None
    assert rows[0] == 0


async def test_an_extractor_round_trips(extractors: PostgresExtractorRepo) -> None:
    created = await extractors.create("Invoices", "line items", SCHEMA, ["body", "subject"])
    stored = await extractors.get(created.id)
    assert stored is not None
    assert stored == created
    assert stored.name == "Invoices"
    assert stored.description == "line items"
    assert stored.schema.document == SCHEMA
    assert stored.source_columns == ("body", "subject")


async def test_a_row_maps_by_column_name_rather_than_position(
    extractors: PostgresExtractorRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shuffled = (
        "updated_at, source_columns, serving_model_id, schema, description, id,"
        " specimen_model_id, created_at, name"
    )
    monkeypatch.setattr(extractors_repo, "COLUMNS", shuffled)
    created = await extractors.create("Invoices", "line items", SCHEMA, ["body", "subject"])
    assert created.name == "Invoices"
    assert created.description == "line items"
    assert created.schema.document == SCHEMA
    assert created.source_columns == ("body", "subject")
    assert await extractors.get(created.id) == created


async def test_an_update_replaces_name_description_and_schema(
    extractors: PostgresExtractorRepo,
) -> None:
    created = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    edited: dict[str, Any] = {"type": "object", "properties": {"currency": {"type": "string"}}}
    replacement = edit(created.schema, edited, "Receipts", "totals")
    updated = await extractors.update(created.id, replacement)
    assert updated is not None
    assert (updated.name, updated.description) == ("Receipts", "totals")
    assert updated.schema.document == edited
    assert updated.source_columns == ("body",)
    assert updated.updated_at >= created.updated_at


async def test_an_update_of_an_absent_extractor_finds_nothing(
    extractors: PostgresExtractorRepo,
) -> None:
    absent = edit(ExtractorSchema.parse(SCHEMA), SCHEMA, "Receipts", "totals")
    assert await extractors.update(4321, absent) is None


async def test_a_deleted_extractor_is_gone(extractors: PostgresExtractorRepo) -> None:
    created = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    assert await extractors.delete(created.id) is True
    assert await extractors.get(created.id) is None
    assert await extractors.delete(created.id) is False


async def test_a_cursor_walks_every_extractor_once(extractors: PostgresExtractorRepo) -> None:
    seeded = [
        (await extractors.create(f"Extractor {index}", "", SCHEMA, ["body"])).id
        for index in range(7)
    ]

    walked: list[int] = []
    after_id: int | None = None
    while True:
        page = await extractors.page(after_id, 3)
        if not page:
            break
        walked.extend(extractor.id for extractor in page)
        after_id = page[-1].id

    assert walked == seeded
    assert len(walked) == len(set(walked))
