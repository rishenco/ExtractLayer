from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from fastapi import APIRouter
from starlette.status import HTTP_201_CREATED

from extractlayer.domain.model import Model
from extractlayer.transport.dto import ModelCreate, ModelView


class _ModelService(Protocol):
    async def create(
        self,
        extractor_id: int,
        specification: Mapping[str, Any],
        known_datasets: Sequence[int],
    ) -> Model: ...

    async def get(self, model_id: int) -> Model: ...

    async def archive(self, model_id: int) -> Model: ...


def model_routes(models: _ModelService) -> APIRouter:
    router = APIRouter(prefix="/models", tags=["models"])

    @router.post("", status_code=HTTP_201_CREATED)
    async def create(payload: ModelCreate) -> ModelView:
        created = await models.create(
            payload.extractor_id, payload.specification, payload.known_datasets
        )
        return ModelView.of(created)

    @router.get("/{model_id}")
    async def get(model_id: int) -> ModelView:
        return ModelView.of(await models.get(model_id))

    @router.post("/{model_id}/archive")
    async def archive(model_id: int) -> ModelView:
        return ModelView.of(await models.archive(model_id))

    return router
