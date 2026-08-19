from __future__ import annotations

from typing import Any

from httpx import ASGITransport, AsyncClient

from extractlayer.config import Config
from extractlayer.main import build_app

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
CREATED = 201


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
            assert sorted(document["paths"]) == ["/extractors", "/extractors/{extractor_id}"]

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
            read = await client.get(f"/extractors/{created.json()['id']}")
            assert read.json() == created.json()
