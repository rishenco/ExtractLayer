from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from fastapi import APIRouter, FastAPI, Query, Response
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from extractlayer.domain.extractor import Extractor
from extractlayer.transport.dto import ExtractorCreate, ExtractorUpdate, ExtractorView
from extractlayer.transport.errors import install_error_handlers

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


class ExtractorService(Protocol):
    async def create(
        self,
        name: str,
        description: str,
        schema: Mapping[str, Any],
        source_columns: Sequence[str],
    ) -> Extractor: ...

    async def get(self, extractor_id: int) -> Extractor: ...

    async def page(self, after_id: int | None, limit: int) -> list[Extractor]: ...

    async def update(
        self,
        extractor_id: int,
        name: str,
        description: str,
        schema: Mapping[str, Any],
    ) -> Extractor: ...

    async def delete(self, extractor_id: int) -> None: ...


def extractor_routes(extractors: ExtractorService) -> APIRouter:
    router = APIRouter(prefix="/extractors", tags=["extractors"])

    @router.post("", status_code=HTTP_201_CREATED)
    async def create(payload: ExtractorCreate) -> ExtractorView:
        created = await extractors.create(
            payload.name, payload.description, payload.document, payload.source_columns
        )
        return ExtractorView.of(created)

    @router.get("")
    async def page(
        limit: int = Query(ge=1),
        after_id: int | None = Query(default=None, ge=1),
    ) -> list[ExtractorView]:
        found = await extractors.page(after_id, limit)
        return [ExtractorView.of(extractor) for extractor in found]

    @router.get("/{extractor_id}")
    async def get(extractor_id: int) -> ExtractorView:
        return ExtractorView.of(await extractors.get(extractor_id))

    @router.put("/{extractor_id}")
    async def update(extractor_id: int, payload: ExtractorUpdate) -> ExtractorView:
        updated = await extractors.update(
            extractor_id, payload.name, payload.description, payload.document
        )
        return ExtractorView.of(updated)

    @router.delete("/{extractor_id}", status_code=HTTP_204_NO_CONTENT)
    async def delete(extractor_id: int) -> Response:
        await extractors.delete(extractor_id)
        return Response(status_code=HTTP_204_NO_CONTENT)

    return router


def create_app(extractors: ExtractorService, lifespan: Lifespan | None = None) -> FastAPI:
    app = FastAPI(title="ExtractLayer", lifespan=lifespan)
    install_error_handlers(app)
    app.include_router(extractor_routes(extractors))
    return app
