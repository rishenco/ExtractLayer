from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from fastapi import APIRouter, Query
from starlette.status import HTTP_201_CREATED

from extractlayer.domain.dataset import Dataset
from extractlayer.domain.dataset_row import DatasetRow, RowWrite
from extractlayer.transport.dto import (
    DatasetCreate,
    DatasetUpdate,
    DatasetView,
    RowBatch,
    RowView,
)


class _DatasetService(Protocol):
    async def create(self, extractor_id: int, name: str, description: str) -> Dataset: ...

    async def page(self, after_id: int | None, limit: int) -> list[Dataset]: ...

    async def update(self, dataset_id: int, name: str, description: str) -> Dataset: ...

    async def rows_of(
        self, dataset_id: int, after_id: int | None, limit: int
    ) -> list[DatasetRow]: ...

    async def write_rows(self, writes: Sequence[RowWrite]) -> list[DatasetRow]: ...


def dataset_routes(datasets: _DatasetService) -> APIRouter:
    router = APIRouter(prefix="/datasets", tags=["datasets"])

    @router.post("", status_code=HTTP_201_CREATED)
    async def create(payload: DatasetCreate) -> DatasetView:
        created = await datasets.create(payload.extractor_id, payload.name, payload.description)
        return DatasetView.of(created)

    @router.get("")
    async def page(
        limit: int = Query(ge=1),
        after_id: int | None = Query(default=None, ge=1),
    ) -> list[DatasetView]:
        found = await datasets.page(after_id, limit)
        return [DatasetView.of(dataset) for dataset in found]

    @router.put("/{dataset_id}")
    async def update(dataset_id: int, payload: DatasetUpdate) -> DatasetView:
        updated = await datasets.update(dataset_id, payload.name, payload.description)
        return DatasetView.of(updated)

    @router.get("/{dataset_id}/rows")
    async def rows(
        dataset_id: int,
        limit: int = Query(ge=1),
        after_id: int | None = Query(default=None, ge=1),
    ) -> list[RowView]:
        found = await datasets.rows_of(dataset_id, after_id, limit)
        return [RowView.of(row) for row in found]

    return router


def row_routes(datasets: _DatasetService) -> APIRouter:
    router = APIRouter(prefix="/rows", tags=["rows"])

    @router.post("")
    async def write(payload: RowBatch) -> list[RowView]:
        landed = await datasets.write_rows([row.as_write() for row in payload.rows])
        return [RowView.of(row) for row in landed]

    return router
