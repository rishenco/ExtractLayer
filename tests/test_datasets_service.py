from __future__ import annotations

from typing import Any

import pytest

from extractlayer.domain.dataset_row import RowSource, RowWrite
from extractlayer.domain.errors import NotFoundError, ValidationError
from extractlayer.service.datasets import DatasetService
from extractlayer.service.extractors import ExtractorService

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
ABSENT = 4321


def write(
    dataset_id: int, row_id: int | None = None, dead: bool = False, **values: Any
) -> RowWrite:
    return RowWrite(id=row_id, dataset_id=dataset_id, values=values, dead=dead)


async def test_a_dataset_round_trips_through_the_service(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    created = await dataset_service.create(extractor.id, "Golden", "hand checked")
    assert await dataset_service.get(created.id) == created

    updated = await dataset_service.update(created.id, "Sampled", "drawn at random")
    assert (updated.name, updated.description) == ("Sampled", "drawn at random")
    assert updated.extractor_id == extractor.id


async def test_a_dataset_of_an_absent_extractor_is_not_created(
    dataset_service: DatasetService,
) -> None:
    with pytest.raises(NotFoundError) as raised:
        await dataset_service.create(ABSENT, "Golden", "")
    assert raised.value.entity == "extractor"


async def test_reading_or_updating_an_absent_dataset_raises_not_found(
    dataset_service: DatasetService,
) -> None:
    with pytest.raises(NotFoundError):
        await dataset_service.get(ABSENT)
    with pytest.raises(NotFoundError):
        await dataset_service.update(ABSENT, "Sampled", "")
    with pytest.raises(NotFoundError):
        await dataset_service.rows_of(ABSENT, None, 10)


async def test_a_cursor_walks_the_dataset_listing_once(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    seeded = [
        (await dataset_service.create(extractor.id, f"Dataset {index}", "")).id
        for index in range(5)
    ]

    walked: list[int] = []
    after_id: int | None = None
    while page := await dataset_service.page(after_id, 2):
        walked.extend(dataset.id for dataset in page)
        after_id = page[-1].id

    assert walked == seeded


async def test_a_written_row_is_normalized_and_marked_human(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "")
    (landed,) = await dataset_service.write_rows([write(dataset.id, body="one")])
    assert landed.values == {"body": "one", "total": None}
    assert landed.source is RowSource.HUMAN


async def test_one_invalid_row_names_its_index_and_lands_nothing(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "")

    with pytest.raises(ValidationError) as raised:
        await dataset_service.write_rows(
            [
                write(dataset.id, body="one", total=1),
                write(dataset.id, total=2),
                write(dataset.id, body="three", total=3),
            ]
        )
    assert raised.value.details == {"rows.1.values.body": "is required"}
    assert await dataset_service.rows_of(dataset.id, None, 10) == []


async def test_a_row_naming_no_dataset_names_its_index(
    dataset_service: DatasetService,
) -> None:
    with pytest.raises(ValidationError) as raised:
        await dataset_service.write_rows([write(ABSENT, body="one")])
    assert "rows.0.dataset_id" in raised.value.details


async def test_a_row_naming_a_row_of_another_dataset_names_its_index(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    mine = await dataset_service.create(extractor.id, "Golden", "")
    theirs = await dataset_service.create(extractor.id, "Sampled", "")
    (landed,) = await dataset_service.write_rows([write(theirs.id, body="one")])

    with pytest.raises(ValidationError) as raised:
        await dataset_service.write_rows([write(mine.id, row_id=landed.id, body="two")])
    assert raised.value.details["rows.0.id"] == f"names no row of dataset {mine.id}"


async def test_a_dead_row_with_no_id_names_its_index(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "")
    with pytest.raises(ValidationError) as raised:
        await dataset_service.write_rows([write(dataset.id, dead=True)])
    assert raised.value.details["rows.0.id"] == "is required to delete a row"


async def test_one_call_inserts_updates_and_deletes_across_two_datasets(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    first = await dataset_service.create(extractor.id, "Golden", "")
    second = await dataset_service.create(extractor.id, "Sampled", "")
    kept, gone = await dataset_service.write_rows(
        [write(first.id, body="one"), write(first.id, body="two")]
    )

    landed = await dataset_service.write_rows(
        [
            write(first.id, row_id=kept.id, body="edited", total=9),
            write(first.id, row_id=gone.id, dead=True),
            write(second.id, body="fresh"),
        ]
    )
    assert [row.dataset_id for row in landed] == [first.id, second.id]
    assert landed[0].values == {"body": "edited", "total": 9}
    assert [row.id for row in await dataset_service.rows_of(first.id, None, 10)] == [kept.id]


async def test_a_cursor_walks_a_datasets_rows_once_through_the_service(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "")
    seeded = [
        row.id
        for row in await dataset_service.write_rows(
            [write(dataset.id, body=f"row {index}") for index in range(5)]
        )
    ]

    walked: list[int] = []
    after_id: int | None = None
    while page := await dataset_service.rows_of(dataset.id, after_id, 2):
        walked.extend(row.id for row in page)
        after_id = page[-1].id

    assert walked == seeded


async def test_a_schema_edit_rewrites_the_rows_a_dataset_already_holds(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "")
    await dataset_service.write_rows([write(dataset.id, body="one", total=1)])

    edited: dict[str, Any] = {"type": "object", "properties": {"currency": {"type": "string"}}}
    await extractor_service.update(extractor.id, "Invoices", "line items", edited, extractor.roles)

    (row,) = await dataset_service.rows_of(dataset.id, None, 10)
    assert row.values == {"body": "one", "currency": None}


async def test_a_batch_naming_one_row_twice_names_the_second_index_and_lands_nothing(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "")
    (landed,) = await dataset_service.write_rows([write(dataset.id, body="one")])

    with pytest.raises(ValidationError) as raised:
        await dataset_service.write_rows(
            [
                write(dataset.id, row_id=landed.id, body="first"),
                write(dataset.id, row_id=landed.id, body="second"),
            ]
        )
    assert raised.value.details == {
        "rows.1.id": f"names row {landed.id}, which an earlier row in this batch names"
    }
    (unchanged,) = await dataset_service.rows_of(dataset.id, None, 10)
    assert unchanged.values["body"] == "one"


async def test_a_batch_updating_and_killing_one_row_is_refused_rather_than_silently_dropped(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "")
    (landed,) = await dataset_service.write_rows([write(dataset.id, body="one")])

    with pytest.raises(ValidationError):
        await dataset_service.write_rows(
            [
                write(dataset.id, row_id=landed.id, body="edited"),
                write(dataset.id, row_id=landed.id, dead=True),
            ]
        )
    assert len(await dataset_service.rows_of(dataset.id, None, 10)) == 1


async def test_written_rows_come_back_in_the_order_the_batch_named_them(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "")
    older = await dataset_service.write_rows(
        [write(dataset.id, body=f"row {index}") for index in range(3)]
    )

    landed = await dataset_service.write_rows(
        [
            write(dataset.id, body="fresh"),
            write(dataset.id, row_id=older[0].id, body="edited"),
            write(dataset.id, body="fresher"),
        ]
    )
    assert [row.values["body"] for row in landed] == ["fresh", "edited", "fresher"]
    assert landed[1].id == older[0].id
    assert landed[0].id > older[-1].id


async def test_a_row_naming_a_source_column_the_schema_also_names_cannot_arise(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "")
    (landed,) = await dataset_service.write_rows([write(dataset.id, body="invoice 7", total=3)])
    assert landed.values == {"body": "invoice 7", "total": 3}
