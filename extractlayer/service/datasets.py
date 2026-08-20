from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Protocol

from extractlayer.domain.dataset import Dataset
from extractlayer.domain.dataset_row import DatasetRow, RowSource, RowWrite
from extractlayer.domain.errors import NotFoundError, ValidationError
from extractlayer.domain.extractor import Extractor

ENTITY = "dataset"


class _DatasetRepo(Protocol):
    async def create(self, extractor_id: int, name: str, description: str) -> Dataset: ...

    async def get(self, dataset_id: int) -> Dataset | None: ...

    async def page(self, after_id: int | None, limit: int) -> list[Dataset]: ...

    async def update(self, dataset_id: int, name: str, description: str) -> Dataset | None: ...


class _RowRepo(Protocol):
    async def page(self, dataset_id: int, after_id: int | None, limit: int) -> list[DatasetRow]: ...

    async def datasets_of(self, row_ids: Sequence[int]) -> dict[int, int]: ...

    async def apply(self, writes: Sequence[RowWrite], source: RowSource) -> list[DatasetRow]: ...


class _ExtractorRepo(Protocol):
    async def get(self, extractor_id: int) -> Extractor | None: ...


class DatasetService:
    def __init__(self, repo: _DatasetRepo, rows: _RowRepo, extractors: _ExtractorRepo) -> None:
        self.repo = repo
        self.rows = rows
        self.extractors = extractors

    async def create(self, extractor_id: int, name: str, description: str) -> Dataset:
        if await self.extractors.get(extractor_id) is None:
            raise NotFoundError("extractor", extractor_id)
        return await self.repo.create(extractor_id, name, description)

    async def get(self, dataset_id: int) -> Dataset:
        dataset = await self.repo.get(dataset_id)
        if dataset is None:
            raise NotFoundError(ENTITY, dataset_id)
        return dataset

    async def page(self, after_id: int | None, limit: int) -> list[Dataset]:
        return await self.repo.page(after_id, limit)

    async def update(self, dataset_id: int, name: str, description: str) -> Dataset:
        updated = await self.repo.update(dataset_id, name, description)
        if updated is None:
            raise NotFoundError(ENTITY, dataset_id)
        return updated

    async def rows_of(self, dataset_id: int, after_id: int | None, limit: int) -> list[DatasetRow]:
        await self.get(dataset_id)
        return await self.rows.page(dataset_id, after_id, limit)

    async def write_rows(self, writes: Sequence[RowWrite]) -> list[DatasetRow]:
        owners = await self._owners(writes)
        ids = [write.id for write in writes if write.id is not None]
        held = await self.rows.datasets_of(ids)
        details: dict[str, str] = {}
        normalized: list[RowWrite] = []
        for index, write in enumerate(writes):
            problem = self._problem(index, write, owners, held)
            if problem:
                details |= problem
                continue
            if write.dead:
                normalized.append(write)
                continue
            try:
                values = owners[write.dataset_id].validated_row(write.values)
            except ValidationError as error:
                details |= error.at(f"rows.{index}.values").details
                continue
            normalized.append(replace(write, values=values))
        if details:
            raise ValidationError(details)
        return await self.rows.apply(normalized, RowSource.HUMAN)

    async def _owners(self, writes: Sequence[RowWrite]) -> dict[int, Extractor]:
        owners: dict[int, Extractor] = {}
        for dataset_id in dict.fromkeys(write.dataset_id for write in writes):
            dataset = await self.repo.get(dataset_id)
            if dataset is None:
                continue
            extractor = await self.extractors.get(dataset.extractor_id)
            if extractor is not None:
                owners[dataset_id] = extractor
        return owners

    @staticmethod
    def _problem(
        index: int,
        write: RowWrite,
        owners: Mapping[int, Extractor],
        held: Mapping[int, int],
    ) -> dict[str, str]:
        at = f"rows.{index}"
        if write.dataset_id not in owners:
            return {f"{at}.dataset_id": "names no dataset"}
        if write.id is not None and held.get(write.id) != write.dataset_id:
            return {f"{at}.id": f"names no row of dataset {write.dataset_id}"}
        if write.dead and write.id is None:
            return {f"{at}.id": "is required to delete a row"}
        return {}
