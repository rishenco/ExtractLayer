from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from extractlayer.domain.errors import ConflictError, NotFoundError
from extractlayer.domain.extractor import Extractor
from extractlayer.domain.model import Model, ModelSpecification

ENTITY = "model"


class _ModelRepo(Protocol):
    async def create(
        self,
        extractor_id: int,
        specification: Mapping[str, Any],
        known_datasets: Sequence[int],
    ) -> Model: ...

    async def get(self, model_id: int) -> Model | None: ...

    async def archive(self, model_id: int) -> Model | None: ...


class _ExtractorRepo(Protocol):
    async def get(self, extractor_id: int) -> Extractor | None: ...


class ModelService:
    def __init__(self, repo: _ModelRepo, extractors: _ExtractorRepo) -> None:
        self.repo = repo
        self.extractors = extractors

    async def create(
        self,
        extractor_id: int,
        specification: Mapping[str, Any],
        known_datasets: Sequence[int],
    ) -> Model:
        if await self.extractors.get(extractor_id) is None:
            raise NotFoundError("extractor", extractor_id)
        parsed = ModelSpecification.parse(specification)
        return await self.repo.create(extractor_id, parsed.document, known_datasets)

    async def get(self, model_id: int) -> Model:
        model = await self.repo.get(model_id)
        if model is None:
            raise NotFoundError(ENTITY, model_id)
        return model

    async def archive(self, model_id: int) -> Model:
        archived = await self.repo.archive(model_id)
        if archived is not None:
            return archived
        model = await self.get(model_id)
        extractor = await self.extractors.get(model.extractor_id)
        if extractor is None:
            raise NotFoundError("extractor", model.extractor_id)
        held = " and ".join(extractor.roles.roles_of(model_id)) or "specimen or serving"
        raise ConflictError(
            f"model {model_id} is the {held} model of extractor {extractor.id},"
            " so it cannot be archived"
        )
