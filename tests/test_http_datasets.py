from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from extractlayer.service.datasets import DatasetService
from extractlayer.service.extractors import ExtractorService
from extractlayer.transport.datasets import dataset_routes, row_routes
from extractlayer.transport.http import create_app, extractor_routes

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
ABSENT = 4321

OK = 200
CREATED = 201
NOT_FOUND = 404
UNPROCESSABLE = 422


@pytest.fixture
async def client(
    extractor_service: ExtractorService, dataset_service: DatasetService
) -> AsyncIterator[AsyncClient]:
    app = create_app(
        [
            extractor_routes(extractor_service),
            dataset_routes(dataset_service),
            row_routes(dataset_service),
        ]
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://extractlayer"
    ) as client:
        yield client


async def extractor(client: AsyncClient) -> int:
    created = await client.post(
        "/extractors",
        json={
            "name": "Invoices",
            "description": "line items",
            "schema": SCHEMA,
            "source_columns": ["body"],
        },
    )
    return int(created.json()["id"])


async def dataset(client: AsyncClient, extractor_id: int, name: str = "Golden") -> int:
    created = await client.post(
        "/datasets",
        json={"extractor_id": extractor_id, "name": name, "description": "hand checked"},
    )
    return int(created.json()["id"])


def row(
    dataset_id: int, row_id: int | None = None, dead: bool = False, **values: Any
) -> dict[str, Any]:
    return {"id": row_id, "dataset_id": dataset_id, "values": values, "dead": dead}


async def test_a_dataset_round_trips_over_rest(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    created = await client.post(
        "/datasets",
        json={"extractor_id": extractor_id, "name": "Golden", "description": "hand checked"},
    )
    assert created.status_code == CREATED
    stored = created.json()
    assert (stored["name"], stored["description"]) == ("Golden", "hand checked")

    read = await client.get(f"/datasets/{stored['id']}")
    assert read.status_code == OK
    assert read.json() == stored


async def test_a_put_replaces_name_and_description_only(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    dataset_id = await dataset(client, extractor_id)
    updated = await client.put(
        f"/datasets/{dataset_id}",
        json={"name": "Sampled", "description": "drawn at random"},
    )
    assert updated.status_code == OK
    assert updated.json()["name"] == "Sampled"
    assert updated.json()["extractor_id"] == extractor_id


async def test_a_put_carrying_the_extractor_is_rejected(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    dataset_id = await dataset(client, extractor_id)
    response = await client.put(
        f"/datasets/{dataset_id}",
        json={"name": "Sampled", "description": "", "extractor_id": extractor_id},
    )
    assert response.status_code == UNPROCESSABLE
    assert "extractor_id" in response.json()["details"]


async def test_a_cursor_walks_the_dataset_listing_once(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    seeded = [await dataset(client, extractor_id, f"Dataset {index}") for index in range(7)]

    walked: list[int] = []
    after_id: int | None = None
    while True:
        query = {"limit": 3} if after_id is None else {"limit": 3, "after_id": after_id}
        page = (await client.get("/datasets", params=query)).json()
        if not page:
            break
        walked.extend(entry["id"] for entry in page)
        after_id = walked[-1]

    assert walked == seeded


async def test_a_dataset_listing_without_a_limit_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/datasets")
    assert response.status_code == UNPROCESSABLE
    assert "limit" in response.json()["details"]


async def test_rows_land_update_and_die_in_one_call_across_two_datasets(
    client: AsyncClient,
) -> None:
    extractor_id = await extractor(client)
    first = await dataset(client, extractor_id, "Golden")
    second = await dataset(client, extractor_id, "Sampled")

    seeded = await client.post(
        "/rows",
        json={"rows": [row(first, body="one", total=1), row(first, body="two", total=2)]},
    )
    assert seeded.status_code == OK
    kept, gone = seeded.json()
    assert kept["source"] == "human"

    landed = await client.post(
        "/rows",
        json={
            "rows": [
                row(first, row_id=kept["id"], body="edited", total=9),
                row(first, row_id=gone["id"], dead=True),
                row(second, body="fresh", total=3),
            ]
        },
    )
    assert landed.status_code == OK
    assert [entry["dataset_id"] for entry in landed.json()] == [first, second]
    assert landed.json()[0]["values"] == {"body": "edited", "total": 9}

    remaining = (await client.get(f"/datasets/{first}/rows", params={"limit": 10})).json()
    assert [entry["id"] for entry in remaining] == [kept["id"]]


async def test_a_missing_derived_column_lands_as_null(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    dataset_id = await dataset(client, extractor_id)
    landed = await client.post("/rows", json={"rows": [row(dataset_id, body="one")]})
    assert landed.json()[0]["values"] == {"body": "one", "total": None}


async def test_one_invalid_row_is_a_422_naming_its_index_and_nothing_lands(
    client: AsyncClient,
) -> None:
    extractor_id = await extractor(client)
    dataset_id = await dataset(client, extractor_id)
    response = await client.post(
        "/rows",
        json={
            "rows": [
                row(dataset_id, body="one", total=1),
                row(dataset_id, total=2),
                row(dataset_id, body="three", total=3),
            ]
        },
    )
    assert response.status_code == UNPROCESSABLE
    assert response.json()["details"] == {"rows.1.values.body": "is required"}

    remaining = (await client.get(f"/datasets/{dataset_id}/rows", params={"limit": 10})).json()
    assert remaining == []


async def test_a_row_naming_no_dataset_is_a_422_naming_its_index(client: AsyncClient) -> None:
    response = await client.post("/rows", json={"rows": [row(ABSENT, body="one")]})
    assert response.status_code == UNPROCESSABLE
    assert response.json()["details"]["rows.0.dataset_id"] == "names no dataset"


@pytest.mark.parametrize("missing", ["id", "dataset_id", "values", "dead"])
async def test_a_row_missing_a_field_is_never_defaulted(client: AsyncClient, missing: str) -> None:
    payload = row(1, body="one")
    del payload[missing]
    response = await client.post("/rows", json={"rows": [payload]})
    assert response.status_code == UNPROCESSABLE
    assert response.json()["details"][f"rows.0.{missing}"] == "Field required"


async def test_a_cursor_walks_a_datasets_rows_once(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    dataset_id = await dataset(client, extractor_id)
    seeded = [
        entry["id"]
        for entry in (
            await client.post(
                "/rows",
                json={"rows": [row(dataset_id, body=f"row {index}") for index in range(7)]},
            )
        ).json()
    ]

    walked: list[int] = []
    after_id: int | None = None
    while True:
        query: dict[str, Any] = {"limit": 3}
        if after_id is not None:
            query["after_id"] = after_id
        page = (await client.get(f"/datasets/{dataset_id}/rows", params=query)).json()
        if not page:
            break
        walked.extend(entry["id"] for entry in page)
        after_id = walked[-1]

    assert walked == seeded


async def test_reading_an_absent_dataset_or_its_rows_is_a_404(client: AsyncClient) -> None:
    assert (await client.get(f"/datasets/{ABSENT}")).status_code == NOT_FOUND
    rows = await client.get(f"/datasets/{ABSENT}/rows", params={"limit": 10})
    assert rows.status_code == NOT_FOUND
    updated = await client.put(f"/datasets/{ABSENT}", json={"name": "x", "description": ""})
    assert updated.status_code == NOT_FOUND


async def test_a_dataset_of_an_absent_extractor_is_a_404(client: AsyncClient) -> None:
    response = await client.post(
        "/datasets", json={"extractor_id": ABSENT, "name": "Golden", "description": ""}
    )
    assert response.status_code == NOT_FOUND


async def test_an_extractor_carries_its_datasets(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    dataset_id = await dataset(client, extractor_id)
    read = (await client.get(f"/extractors/{extractor_id}")).json()
    assert read["datasets"] == [{"id": dataset_id, "name": "Golden", "description": "hand checked"}]


async def test_a_schema_edit_rewrites_the_rows_a_dataset_holds(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    dataset_id = await dataset(client, extractor_id)
    await client.post("/rows", json={"rows": [row(dataset_id, body="one", total=1)]})

    edited: dict[str, Any] = {"type": "object", "properties": {"currency": {"type": "string"}}}
    replaced = await client.put(
        f"/extractors/{extractor_id}",
        json={
            "name": "Invoices",
            "description": "line items",
            "schema": edited,
            "specimen_model_id": None,
            "serving_model_id": None,
        },
    )
    assert replaced.status_code == OK

    remaining = (await client.get(f"/datasets/{dataset_id}/rows", params={"limit": 10})).json()
    assert remaining[0]["values"] == {"body": "one", "currency": None}
