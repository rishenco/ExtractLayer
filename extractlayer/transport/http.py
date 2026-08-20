from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from fastapi import APIRouter, FastAPI, Query, Response
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from extractlayer.domain.extractor import Extractor, ExtractorDetail, ModelRoles
from extractlayer.transport.dto import (
    ExtractorCreate,
    ExtractorDetailView,
    ExtractorUpdate,
    ExtractorView,
    ServeRequest,
    ServeView,
)
from extractlayer.transport.errors import install_error_handlers

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


class _ExtractorService(Protocol):
    async def create(
        self,
        name: str,
        description: str,
        schema: Mapping[str, Any],
        source_columns: Sequence[str],
    ) -> Extractor: ...

    async def detail(self, extractor_id: int) -> ExtractorDetail: ...

    async def page(self, after_id: int | None, limit: int) -> list[Extractor]: ...

    async def update(
        self,
        extractor_id: int,
        name: str,
        description: str,
        schema: Mapping[str, Any],
        roles: ModelRoles,
    ) -> Extractor: ...

    async def delete(self, extractor_id: int) -> None: ...

    async def serve(
        self, extractor_id: int, source_values: Mapping[str, Any]
    ) -> dict[str, Any]: ...


def extractor_routes(extractors: _ExtractorService) -> APIRouter:
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
    async def get(extractor_id: int) -> ExtractorDetailView:
        return ExtractorDetailView.of_detail(await extractors.detail(extractor_id))

    @router.put("/{extractor_id}")
    async def update(extractor_id: int, payload: ExtractorUpdate) -> ExtractorView:
        updated = await extractors.update(
            extractor_id,
            payload.name,
            payload.description,
            payload.document,
            ModelRoles(payload.specimen_model_id, payload.serving_model_id),
        )
        return ExtractorView.of(updated)

    @router.delete("/{extractor_id}", status_code=HTTP_204_NO_CONTENT)
    async def delete(extractor_id: int) -> Response:
        await extractors.delete(extractor_id)
        return Response(status_code=HTTP_204_NO_CONTENT)

    @router.post("/{extractor_id}/serve")
    async def serve(extractor_id: int, payload: ServeRequest) -> ServeView:
        derived = await extractors.serve(extractor_id, payload.source_values)
        return ServeView(derived_values=derived)

    return router


def create_app(routers: Sequence[APIRouter], lifespan: Lifespan | None = None) -> FastAPI:
    app = FastAPI(title="ExtractLayer", lifespan=lifespan)
    install_error_handlers(app)
    for router in routers:
        app.include_router(router)
    return app
