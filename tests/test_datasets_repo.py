from __future__ import annotations

from typing import Any

from extractlayer.domain.dataset_row import RowSource, RowWrite
from extractlayer.domain.extractor import Extractor, ExtractorEdit, ModelRoles
from extractlayer.domain.schema import ExtractorSchema
from extractlayer.repo.pg.datasets import PostgresDatasetRepo
from extractlayer.repo.pg.extractors import PostgresExtractorRepo
from extractlayer.repo.pg.rows import PostgresRowRepo

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}


def schema_edit(extractor: Extractor, document: dict[str, Any]) -> ExtractorEdit:
    return ExtractorEdit(
        name=extractor.name,
        description=extractor.description,
        schema=ExtractorSchema.parse(document),
        previous=extractor.schema,
        roles=ModelRoles(specimen_model_id=None, serving_model_id=None),
    )


def write(
    dataset_id: int, row_id: int | None = None, dead: bool = False, **values: Any
) -> RowWrite:
    return RowWrite(
        id=row_id,
        dataset_id=dataset_id,
        values=values,
        dead=dead,
    )


async def test_a_dataset_round_trips(
    extractors: PostgresExtractorRepo, datasets: PostgresDatasetRepo
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    created = await datasets.create(extractor.id, "Golden", "hand checked")
    stored = await datasets.get(created.id)
    assert stored == created
    assert stored is not None
    assert (stored.extractor_id, stored.name, stored.description) == (
        extractor.id,
        "Golden",
        "hand checked",
    )


async def test_an_update_replaces_name_and_description_but_not_the_extractor(
    extractors: PostgresExtractorRepo, datasets: PostgresDatasetRepo
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    created = await datasets.create(extractor.id, "Golden", "hand checked")
    updated = await datasets.update(created.id, "Sampled", "drawn at random")
    assert updated is not None
    assert (updated.name, updated.description) == ("Sampled", "drawn at random")
    assert updated.extractor_id == extractor.id
    assert updated.updated_at >= created.updated_at


async def test_an_update_of_an_absent_dataset_finds_nothing(datasets: PostgresDatasetRepo) -> None:
    assert await datasets.update(4321, "Sampled", "drawn at random") is None


async def test_a_cursor_walks_every_dataset_once(
    extractors: PostgresExtractorRepo, datasets: PostgresDatasetRepo
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    seeded = [
        (await datasets.create(extractor.id, f"Dataset {index}", "")).id for index in range(7)
    ]

    walked: list[int] = []
    after_id: int | None = None
    while page := await datasets.page(after_id, 3):
        walked.extend(dataset.id for dataset in page)
        after_id = page[-1].id

    assert walked == seeded
    assert len(walked) == len(set(walked))


async def test_the_datasets_of_an_extractor_exclude_another_extractors(
    extractors: PostgresExtractorRepo, datasets: PostgresDatasetRepo
) -> None:
    mine = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    theirs = await extractors.create("Receipts", "totals", SCHEMA, ["body"])
    kept = await datasets.create(mine.id, "Golden", "hand checked")
    await datasets.create(theirs.id, "Golden", "hand checked")
    assert [dataset.id for dataset in await datasets.for_extractor(mine.id)] == [kept.id]


async def test_rows_land_across_more_than_one_dataset_in_one_call(
    extractors: PostgresExtractorRepo,
    datasets: PostgresDatasetRepo,
    rows: PostgresRowRepo,
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    first = await datasets.create(extractor.id, "Golden", "")
    second = await datasets.create(extractor.id, "Sampled", "")

    landed = await rows.apply(
        [write(first.id, body="one", total=1), write(second.id, body="two", total=2)],
        RowSource.HUMAN,
    )
    assert [row.dataset_id for row in landed] == [first.id, second.id]
    assert [row.source for row in landed] == [RowSource.HUMAN, RowSource.HUMAN]
    assert [row.values["body"] for row in landed] == ["one", "two"]


async def test_a_row_carrying_an_id_is_updated_and_one_carrying_dead_is_deleted(
    extractors: PostgresExtractorRepo,
    datasets: PostgresDatasetRepo,
    rows: PostgresRowRepo,
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await datasets.create(extractor.id, "Golden", "")
    kept, gone = await rows.apply(
        [write(dataset.id, body="one", total=1), write(dataset.id, body="two", total=2)],
        RowSource.HUMAN,
    )

    landed = await rows.apply(
        [
            write(dataset.id, row_id=kept.id, body="edited", total=9),
            write(dataset.id, row_id=gone.id, dead=True),
        ],
        RowSource.HUMAN,
    )
    assert [row.id for row in landed] == [kept.id]
    assert landed[0].values == {"body": "edited", "total": 9}

    remaining = await rows.page(dataset.id, None, 10)
    assert [row.id for row in remaining] == [kept.id]


async def test_the_dataset_of_each_row_id_is_reported_before_a_batch_is_applied(
    extractors: PostgresExtractorRepo,
    datasets: PostgresDatasetRepo,
    rows: PostgresRowRepo,
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await datasets.create(extractor.id, "Golden", "")
    (landed,) = await rows.apply([write(dataset.id, body="one", total=1)], RowSource.HUMAN)
    assert await rows.datasets_of([landed.id, 4321]) == {landed.id: dataset.id}
    assert await rows.datasets_of([]) == {}


async def test_a_cursor_walks_a_datasets_rows_once(
    extractors: PostgresExtractorRepo,
    datasets: PostgresDatasetRepo,
    rows: PostgresRowRepo,
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await datasets.create(extractor.id, "Golden", "")
    other = await datasets.create(extractor.id, "Sampled", "")
    seeded = [
        row.id
        for row in await rows.apply(
            [write(dataset.id, body=f"row {index}", total=index) for index in range(7)],
            RowSource.HUMAN,
        )
    ]
    await rows.apply([write(other.id, body="elsewhere", total=0)], RowSource.HUMAN)

    walked: list[int] = []
    after_id: int | None = None
    while page := await rows.page(dataset.id, after_id, 3):
        walked.extend(row.id for row in page)
        after_id = page[-1].id

    assert walked == seeded


async def test_a_schema_edit_rewrites_the_rows_of_every_dataset_it_owns(
    extractors: PostgresExtractorRepo,
    datasets: PostgresDatasetRepo,
    rows: PostgresRowRepo,
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await datasets.create(extractor.id, "Golden", "")
    (before,) = await rows.apply([write(dataset.id, body="one", total=1)], RowSource.HUMAN)

    edited: dict[str, Any] = {
        "type": "object",
        "properties": {"currency": {"type": "string"}},
    }
    await extractors.update(extractor.id, schema_edit(extractor, edited))

    (after,) = await rows.page(dataset.id, None, 10)
    assert after.id == before.id
    assert after.values == {"body": "one", "currency": None}


async def test_a_schema_edit_leaves_another_extractors_rows_alone(
    extractors: PostgresExtractorRepo,
    datasets: PostgresDatasetRepo,
    rows: PostgresRowRepo,
) -> None:
    mine = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    theirs = await extractors.create("Receipts", "totals", SCHEMA, ["body"])
    dataset = await datasets.create(theirs.id, "Golden", "")
    await rows.apply([write(dataset.id, body="one", total=1)], RowSource.HUMAN)

    edited: dict[str, Any] = {"type": "object", "properties": {"currency": {"type": "string"}}}
    await extractors.update(mine.id, schema_edit(mine, edited))

    (untouched,) = await rows.page(dataset.id, None, 10)
    assert untouched.values == {"body": "one", "total": 1}


async def test_deleting_an_extractor_takes_its_datasets_and_their_rows(
    extractors: PostgresExtractorRepo,
    datasets: PostgresDatasetRepo,
    rows: PostgresRowRepo,
) -> None:
    extractor = await extractors.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await datasets.create(extractor.id, "Golden", "")
    await rows.apply([write(dataset.id, body="one", total=1)], RowSource.HUMAN)

    assert await extractors.delete(extractor.id) is True
    assert await datasets.get(dataset.id) is None
    assert await rows.page(dataset.id, None, 10) == []
