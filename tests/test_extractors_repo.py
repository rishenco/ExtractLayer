from __future__ import annotations

from typing import Any

import psycopg

from extractlayer.repo.extractors import PostgresExtractorRepo
from extractlayer.repo.postgres import apply_migrations

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}


def test_migrations_build_the_schema_from_an_empty_database(empty_database: str) -> None:
    apply_migrations(empty_database)
    with psycopg.connect(empty_database) as connection:
        table = connection.execute("SELECT to_regclass('extractlayer.extractors')").fetchone()
        columns = connection.execute(
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_schema = 'extractlayer' AND table_name = 'extractors'"
            " ORDER BY column_name"
        ).fetchall()
    assert table is not None
    assert table[0] == "extractlayer.extractors"
    assert [column[0] for column in columns] == [
        "created_at",
        "description",
        "id",
        "name",
        "schema",
        "source_columns",
        "updated_at",
    ]


def test_migrations_are_safe_to_re_run(empty_database: str) -> None:
    apply_migrations(empty_database)
    apply_migrations(empty_database)
    with psycopg.connect(empty_database) as connection:
        applied = connection.execute("SELECT count(*) FROM _yoyo_migration").fetchone()
        rows = connection.execute("SELECT count(*) FROM extractlayer.extractors").fetchone()
    assert applied is not None
    assert applied[0] == 1
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


async def test_an_update_replaces_name_description_and_schema(
    extractors: PostgresExtractorRepo,
) -> None:
    created = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    edited: dict[str, Any] = {"type": "object", "properties": {"currency": {"type": "string"}}}
    updated = await extractors.update(created.id, "Receipts", "totals", edited)
    assert updated is not None
    assert (updated.name, updated.description) == ("Receipts", "totals")
    assert updated.schema.document == edited
    assert updated.source_columns == ("body",)
    assert updated.updated_at >= created.updated_at


async def test_an_update_of_an_absent_extractor_finds_nothing(
    extractors: PostgresExtractorRepo,
) -> None:
    assert await extractors.update(4321, "Receipts", "totals", SCHEMA) is None


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
