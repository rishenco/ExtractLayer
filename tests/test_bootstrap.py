from __future__ import annotations

from typing import Any

from httpx import ASGITransport, AsyncClient

from extractlayer.config import Config
from extractlayer.main import build_app

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
CREATED = 201
OK = 200


async def test_the_composition_root_serves_the_api_from_an_empty_database(
    empty_database: str,
) -> None:
    config = Config(database_url=empty_database, host="127.0.0.1", api_port=8420)
    app = build_app(config)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://extractlayer") as client:
            document = (await client.get("/openapi.json")).json()
            assert document["info"]["title"] == "ExtractLayer"
            assert sorted(document["paths"]) == [
                "/datasets",
                "/datasets/{dataset_id}",
                "/datasets/{dataset_id}/rows",
                "/extractors",
                "/extractors/{extractor_id}",
                "/extractors/{extractor_id}/serve",
                "/models",
                "/models/{model_id}",
                "/models/{model_id}/archive",
                "/rows",
            ]

            created = await client.post(
                "/extractors",
                json={
                    "name": "Invoices",
                    "description": "line items",
                    "schema": SCHEMA,
                    "source_columns": ["body"],
                },
            )
            assert created.status_code == CREATED
            extractor_id = created.json()["id"]
            model = await client.post(
                "/models",
                json={
                    "extractor_id": extractor_id,
                    "specification": {"kind": "dummy"},
                    "known_datasets": [],
                },
            )
            assert model.status_code == CREATED
            replaced = await client.put(
                f"/extractors/{extractor_id}",
                json={
                    "name": "Invoices",
                    "description": "line items",
                    "schema": SCHEMA,
                    "specimen_model_id": None,
                    "serving_model_id": model.json()["id"],
                },
            )
            assert replaced.status_code == OK

            served = await client.post(
                f"/extractors/{extractor_id}/serve",
                json={"source_values": {"body": "invoice 7"}},
            )
            assert served.status_code == OK
            assert served.json() == {"derived_values": {"total": None}}
