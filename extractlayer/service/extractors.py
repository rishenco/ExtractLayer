from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from extractlayer.domain.errors import NotFoundError
from extractlayer.domain.extractor import Extractor
from extractlayer.domain.schema import ExtractorSchema

ENTITY = "extractor"


class ExtractorRepo(Protocol):
    async def create(
        self,
        name: str,
        description: str,
        schema: Mapping[str, Any],
        source_columns: Sequence[str],
    ) -> Extractor: ...

    async def get(self, extractor_id: int) -> Extractor | None: ...

    async def page(self, after_id: int | None, limit: int) -> list[Extractor]: ...

    async def update(
        self,
        extractor_id: int,
        name: str,
        description: str,
        schema: Mapping[str, Any],
    ) -> Extractor | None: ...

    async def delete(self, extractor_id: int) -> bool: ...


class ExtractorService:
    def __init__(self, repo: ExtractorRepo) -> None:
        self.repo = repo

    async def create(
        self,
        name: str,
        description: str,
        schema: Mapping[str, Any],
        source_columns: Sequence[str],
    ) -> Extractor:
        parsed = ExtractorSchema.parse(schema)
        return await self.repo.create(name, description, parsed.document, source_columns)

    async def get(self, extractor_id: int) -> Extractor:
        extractor = await self.repo.get(extractor_id)
        if extractor is None:
            raise NotFoundError(ENTITY, extractor_id)
        return extractor

    async def page(self, after_id: int | None, limit: int) -> list[Extractor]:
        return await self.repo.page(after_id, limit)

    async def update(
        self,
        extractor_id: int,
        name: str,
        description: str,
        schema: Mapping[str, Any],
    ) -> Extractor:
        current = await self.get(extractor_id)
        edited = ExtractorSchema.edited(current.schema, schema)
        updated = await self.repo.update(extractor_id, name, description, edited.document)
        if updated is None:
            raise NotFoundError(ENTITY, extractor_id)
        return updated

    async def delete(self, extractor_id: int) -> None:
        if not await self.repo.delete(extractor_id):
            raise NotFoundError(ENTITY, extractor_id)
