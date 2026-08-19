from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from extractlayer.repo.extractors import PostgresExtractorRepo
from extractlayer.service.extractors import ExtractorService
from extractlayer.transport.http import create_app

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
ABSENT = 4321

OK = 200
CREATED = 201
NO_CONTENT = 204
NOT_FOUND = 404
UNPROCESSABLE = 422


def body(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "Invoices",
        "description": "line items",
        "schema": SCHEMA,
        "source_columns": ["body", "subject"],
    }
    payload.update(overrides)
    return payload


@pytest.fixture
async def client(extractors: PostgresExtractorRepo) -> AsyncIterator[AsyncClient]:
    app = create_app(ExtractorService(extractors))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://extractlayer"
    ) as client:
        yield client


async def test_an_extractor_round_trips_over_rest(client: AsyncClient) -> None:
    created = await client.post("/extractors", json=body())
    assert created.status_code == CREATED
    stored = created.json()
    assert stored["name"] == "Invoices"
    assert stored["schema"] == SCHEMA
    assert stored["source_columns"] == ["body", "subject"]

    read = await client.get(f"/extractors/{stored['id']}")
    assert read.status_code == OK
    assert read.json() == stored


async def test_a_put_replaces_name_description_and_schema(client: AsyncClient) -> None:
    created = (await client.post("/extractors", json=body())).json()
    edited: dict[str, Any] = {"type": "object", "properties": {"currency": {"type": "string"}}}
    updated = await client.put(
        f"/extractors/{created['id']}",
        json={"name": "Receipts", "description": "totals", "schema": edited},
    )
    assert updated.status_code == OK
    assert updated.json()["name"] == "Receipts"
    assert updated.json()["description"] == "totals"
    assert updated.json()["schema"] == edited
    assert updated.json()["source_columns"] == ["body", "subject"]


async def test_a_deleted_extractor_is_not_found_afterwards(client: AsyncClient) -> None:
    created = (await client.post("/extractors", json=body())).json()
    deleted = await client.delete(f"/extractors/{created['id']}")
    assert deleted.status_code == NO_CONTENT
    assert (await client.get(f"/extractors/{created['id']}")).status_code == NOT_FOUND


async def test_a_cursor_walks_the_listing_once(client: AsyncClient) -> None:
    seeded = [
        (await client.post("/extractors", json=body(name=f"Extractor {index}"))).json()["id"]
        for index in range(7)
    ]

    walked: list[int] = []
    after_id: int | None = None
    while True:
        query = {"limit": 3} if after_id is None else {"limit": 3, "after_id": after_id}
        page = (await client.get("/extractors", params=query)).json()
        if not page:
            break
        walked.extend(extractor["id"] for extractor in page)
        after_id = walked[-1]

    assert walked == seeded
    assert len(walked) == len(set(walked))


async def test_a_listing_without_a_limit_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/extractors")
    assert response.status_code == UNPROCESSABLE
    assert "limit" in response.json()["details"]


async def test_a_put_carrying_source_columns_is_rejected(client: AsyncClient) -> None:
    created = (await client.post("/extractors", json=body())).json()
    response = await client.put(
        f"/extractors/{created['id']}",
        json={
            "name": "Receipts",
            "description": "totals",
            "schema": SCHEMA,
            "source_columns": ["body"],
        },
    )
    assert response.status_code == UNPROCESSABLE
    assert "source_columns" in response.json()["details"]

    unchanged = (await client.get(f"/extractors/{created['id']}")).json()
    assert unchanged["name"] == "Invoices"
    assert unchanged["source_columns"] == ["body", "subject"]


@pytest.mark.parametrize("missing", ["name", "description", "schema", "source_columns"])
async def test_a_create_missing_a_field_is_rejected_by_name(
    client: AsyncClient, missing: str
) -> None:
    payload = body()
    del payload[missing]
    response = await client.post("/extractors", json=payload)
    assert response.status_code == UNPROCESSABLE
    assert response.json()["details"][missing] == "Field required"


async def test_a_missing_field_is_never_defaulted(client: AsyncClient) -> None:
    response = await client.post("/extractors", json={"name": "Invoices"})
    assert response.status_code == UNPROCESSABLE
    assert sorted(response.json()["details"]) == ["description", "schema", "source_columns"]


async def test_not_found_maps_to_404_on_every_route(client: AsyncClient) -> None:
    assert (await client.get(f"/extractors/{ABSENT}")).status_code == NOT_FOUND
    assert (await client.delete(f"/extractors/{ABSENT}")).status_code == NOT_FOUND
    put = await client.put(
        f"/extractors/{ABSENT}",
        json={"name": "Receipts", "description": "totals", "schema": SCHEMA},
    )
    assert put.status_code == NOT_FOUND
    assert put.json()["error"] == f"extractor {ABSENT} does not exist"


async def test_a_domain_validation_error_maps_to_422_with_its_details(
    client: AsyncClient,
) -> None:
    response = await client.post("/extractors", json=body(schema={"type": "object"}))
    assert response.status_code == UNPROCESSABLE
    assert response.json()["details"]["schema.properties"] == "must declare at least one column"


async def test_a_schema_edit_changing_a_column_type_is_refused_over_rest(
    client: AsyncClient,
) -> None:
    created = (await client.post("/extractors", json=body())).json()
    changed: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "string"}}}
    response = await client.put(
        f"/extractors/{created['id']}",
        json={"name": "Invoices", "description": "line items", "schema": changed},
    )
    assert response.status_code == UNPROCESSABLE
    assert 'cannot change from {"type": "number"} to {"type": "string"}' in (
        response.json()["details"]["schema.properties.total.type"]
    )


async def test_a_schema_edit_changing_an_array_element_type_is_refused_over_rest(
    client: AsyncClient,
) -> None:
    created = (
        await client.post(
            "/extractors",
            json=body(
                schema={
                    "type": "object",
                    "properties": {"lines": {"type": "array", "items": {"type": "string"}}},
                }
            ),
        )
    ).json()
    changed: dict[str, Any] = {
        "type": "object",
        "properties": {"lines": {"type": "array", "items": {"type": "number"}}},
    }
    response = await client.put(
        f"/extractors/{created['id']}",
        json={"name": "Invoices", "description": "line items", "schema": changed},
    )
    assert response.status_code == UNPROCESSABLE
    assert "schema.properties.lines.type" in response.json()["details"]


async def test_the_openapi_document_names_the_schema_field(client: AsyncClient) -> None:
    document = (await client.get("/openapi.json")).json()
    view = document["components"]["schemas"]["ExtractorView"]["properties"]
    assert "schema" in view
    assert "document" not in view
