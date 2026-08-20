from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from extractlayer.domain.dataset import Dataset
from extractlayer.domain.errors import (
    ConflictError,
    NotFoundError,
    UpstreamModelError,
    ValidationError,
)
from extractlayer.domain.extractor import Extractor, ExtractorDetail, ExtractorEdit, ModelRoles
from extractlayer.domain.model import Model, ModelKind, ModelSpecification
from extractlayer.domain.schema import ExtractorSchema

ENTITY = "extractor"


class _ExtractorRepo(Protocol):
    async def create(
        self,
        name: str,
        description: str,
        schema: Mapping[str, Any],
        source_columns: Sequence[str],
    ) -> Extractor: ...

    async def get(self, extractor_id: int) -> Extractor | None: ...

    async def page(self, after_id: int | None, limit: int) -> list[Extractor]: ...

    async def update(self, extractor_id: int, edit: ExtractorEdit) -> Extractor | None: ...

    async def delete(self, extractor_id: int) -> bool: ...


class _ModelRepo(Protocol):
    async def get(self, model_id: int) -> Model | None: ...

    async def live_for_extractor(self, extractor_id: int) -> list[Model]: ...


class _DatasetRepo(Protocol):
    async def for_extractor(self, extractor_id: int) -> list[Dataset]: ...


class _ModelExecutor(Protocol):
    async def run(
        self,
        specification: ModelSpecification,
        schema: ExtractorSchema,
        source_values: Mapping[str, str],
        /,
    ) -> Mapping[str, Any]: ...


class ExtractorService:
    def __init__(
        self,
        repo: _ExtractorRepo,
        models: _ModelRepo,
        datasets: _DatasetRepo,
        executors: Mapping[ModelKind, _ModelExecutor],
    ) -> None:
        self.repo = repo
        self.models = models
        self.datasets = datasets
        self.executors = executors

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

    async def detail(self, extractor_id: int) -> ExtractorDetail:
        extractor = await self.get(extractor_id)
        return ExtractorDetail(
            extractor=extractor,
            datasets=tuple(await self.datasets.for_extractor(extractor_id)),
            models=tuple(await self.models.live_for_extractor(extractor_id)),
        )

    async def page(self, after_id: int | None, limit: int) -> list[Extractor]:
        return await self.repo.page(after_id, limit)

    async def update(
        self,
        extractor_id: int,
        name: str,
        description: str,
        schema: Mapping[str, Any],
        roles: ModelRoles,
    ) -> Extractor:
        current = await self.get(extractor_id)
        edited = ExtractorSchema.edited(current.schema, schema)
        await self._check_roles(extractor_id, roles)
        edit = ExtractorEdit(
            name=name,
            description=description,
            schema=edited,
            previous=current.schema,
            roles=roles,
        )
        updated = await self.repo.update(extractor_id, edit)
        if updated is None:
            raise NotFoundError(ENTITY, extractor_id)
        return updated

    async def delete(self, extractor_id: int) -> None:
        if not await self.repo.delete(extractor_id):
            raise NotFoundError(ENTITY, extractor_id)

    async def serve(self, extractor_id: int, source_values: Mapping[str, Any]) -> dict[str, Any]:
        extractor = await self.get(extractor_id)
        try:
            values = extractor.validated_source_values(source_values)
        except ValidationError as error:
            raise error.at("source_values") from error

        model_id = extractor.roles.serving
        if model_id is None:
            raise ConflictError(
                f"extractor {extractor_id} names neither a serving nor a specimen model,"
                " so it cannot serve"
            )
        model = await self.models.get(model_id)
        if model is None:
            raise NotFoundError("model", model_id)

        produced = await self.executors[model.kind].run(
            model.specification, extractor.schema, values
        )
        try:
            return extractor.schema.derived_values(produced)
        except ValidationError as error:
            raise UpstreamModelError(
                f"model {model.id} returned a row extractor {extractor_id} rejects: {error}"
            ) from error

    async def _check_roles(self, extractor_id: int, roles: ModelRoles) -> None:
        details: dict[str, str] = {}
        for field, model_id in roles.by_field.items():
            if model_id is None:
                continue
            model = await self.models.get(model_id)
            if model is None:
                details[field] = f"names no model, so extractor {extractor_id} cannot hold it"
            elif model.extractor_id != extractor_id:
                details[field] = f"names a model of extractor {model.extractor_id}"
            elif model.is_archived:
                details[field] = "names an archived model"
        if details:
            raise ValidationError(details)
