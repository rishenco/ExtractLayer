from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from extractlayer.service.extractors import ExtractorService
from extractlayer.service.models import ModelService
from extractlayer.transport.http import create_app, extractor_routes
from extractlayer.transport.models import model_routes

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
SPECIFICATION: dict[str, Any] = {"kind": "dummy", "prompt": "read it"}
ABSENT = 4321

OK = 200
CREATED = 201
BAD_REQUEST = 400
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
UNPROCESSABLE = 422


@pytest.fixture
async def client(
    extractor_service: ExtractorService, model_service: ModelService
) -> AsyncIterator[AsyncClient]:
    app = create_app([extractor_routes(extractor_service), model_routes(model_service)])
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


def roles(specimen: int | None = None, serving: int | None = None) -> dict[str, Any]:
    return {
        "name": "Invoices",
        "description": "line items",
        "schema": SCHEMA,
        "specimen_model_id": specimen,
        "serving_model_id": serving,
    }


async def test_a_model_round_trips_over_rest(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    created = await client.post(
        "/models",
        json={
            "extractor_id": extractor_id,
            "specification": SPECIFICATION,
            "known_datasets": [],
        },
    )
    assert created.status_code == CREATED
    stored = created.json()
    assert stored["specification"] == SPECIFICATION
    assert stored["archived_at"] is None

    read = await client.get(f"/models/{stored['id']}")
    assert read.status_code == OK
    assert read.json() == stored


async def test_no_update_route_exists_for_a_model(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    created = (
        await client.post(
            "/models",
            json={
                "extractor_id": extractor_id,
                "specification": SPECIFICATION,
                "known_datasets": [],
            },
        )
    ).json()
    for call in (client.put, client.patch, client.delete):
        assert (await call(f"/models/{created['id']}")).status_code == METHOD_NOT_ALLOWED


async def test_a_specification_naming_an_unknown_kind_is_a_422(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    response = await client.post(
        "/models",
        json={
            "extractor_id": extractor_id,
            "specification": {"kind": "psychic"},
            "known_datasets": [],
        },
    )
    assert response.status_code == UNPROCESSABLE
    assert "unknown model kind" in response.json()["details"]["specification.kind"]


async def test_an_archived_model_still_reads(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    created = (
        await client.post(
            "/models",
            json={
                "extractor_id": extractor_id,
                "specification": SPECIFICATION,
                "known_datasets": [],
            },
        )
    ).json()

    archived = await client.post(f"/models/{created['id']}/archive")
    assert archived.status_code == OK
    assert archived.json()["archived_at"] is not None

    read = await client.get(f"/models/{created['id']}")
    assert read.status_code == OK
    assert read.json()["archived_at"] == archived.json()["archived_at"]


async def test_archiving_a_model_a_role_names_is_a_named_400(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    created = (
        await client.post(
            "/models",
            json={
                "extractor_id": extractor_id,
                "specification": SPECIFICATION,
                "known_datasets": [],
            },
        )
    ).json()
    assert (
        await client.put(f"/extractors/{extractor_id}", json=roles(serving=created["id"]))
    ).status_code == OK

    refused = await client.post(f"/models/{created['id']}/archive")
    assert refused.status_code == BAD_REQUEST
    assert refused.json()["error"] == (
        f"model {created['id']} is the serving model of extractor {extractor_id},"
        " so it cannot be archived"
    )


async def test_setting_an_archived_model_as_a_role_is_a_422(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    created = (
        await client.post(
            "/models",
            json={
                "extractor_id": extractor_id,
                "specification": SPECIFICATION,
                "known_datasets": [],
            },
        )
    ).json()
    await client.post(f"/models/{created['id']}/archive")

    refused = await client.put(f"/extractors/{extractor_id}", json=roles(specimen=created["id"]))
    assert refused.status_code == UNPROCESSABLE
    assert refused.json()["details"]["specimen_model_id"] == "names an archived model"


async def test_a_role_naming_another_extractors_model_is_rejected_by_name(
    client: AsyncClient,
) -> None:
    mine = await extractor(client)
    theirs = await extractor(client)
    created = (
        await client.post(
            "/models",
            json={"extractor_id": theirs, "specification": SPECIFICATION, "known_datasets": []},
        )
    ).json()

    refused = await client.put(f"/extractors/{mine}", json=roles(serving=created["id"]))
    assert refused.status_code == UNPROCESSABLE
    assert refused.json()["details"]["serving_model_id"] == f"names a model of extractor {theirs}"


async def test_a_model_of_an_absent_extractor_is_a_404(client: AsyncClient) -> None:
    response = await client.post(
        "/models",
        json={"extractor_id": ABSENT, "specification": SPECIFICATION, "known_datasets": []},
    )
    assert response.status_code == NOT_FOUND


async def test_reading_or_archiving_an_absent_model_is_a_404(client: AsyncClient) -> None:
    assert (await client.get(f"/models/{ABSENT}")).status_code == NOT_FOUND
    assert (await client.post(f"/models/{ABSENT}/archive")).status_code == NOT_FOUND


@pytest.mark.parametrize("missing", ["extractor_id", "specification", "known_datasets"])
async def test_a_model_create_missing_a_field_is_rejected_by_name(
    client: AsyncClient, missing: str
) -> None:
    payload: dict[str, Any] = {
        "extractor_id": 1,
        "specification": SPECIFICATION,
        "known_datasets": [],
    }
    del payload[missing]
    response = await client.post("/models", json=payload)
    assert response.status_code == UNPROCESSABLE
    assert response.json()["details"][missing] == "Field required"


async def test_an_extractor_carries_its_datasets_and_live_models(client: AsyncClient) -> None:
    extractor_id = await extractor(client)
    kept = (
        await client.post(
            "/models",
            json={
                "extractor_id": extractor_id,
                "specification": SPECIFICATION,
                "known_datasets": [3],
            },
        )
    ).json()
    hidden = (
        await client.post(
            "/models",
            json={
                "extractor_id": extractor_id,
                "specification": SPECIFICATION,
                "known_datasets": [],
            },
        )
    ).json()
    await client.post(f"/models/{hidden['id']}/archive")

    read = (await client.get(f"/extractors/{extractor_id}")).json()
    assert read["models"] == [{"id": kept["id"], "kind": "dummy", "known_datasets": [3]}]
    assert read["datasets"] == []
