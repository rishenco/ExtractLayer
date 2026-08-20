from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from extractlayer.domain.dataset import Dataset
from extractlayer.domain.errors import ValidationError
from extractlayer.domain.model import Model
from extractlayer.domain.schema import ExtractorSchema


@dataclass(frozen=True)
class ModelRoles:
    specimen_model_id: int | None
    serving_model_id: int | None

    @property
    def serving(self) -> int | None:
        return self.serving_model_id or self.specimen_model_id

    @property
    def by_field(self) -> Mapping[str, int | None]:
        return {
            "specimen_model_id": self.specimen_model_id,
            "serving_model_id": self.serving_model_id,
        }

    def roles_of(self, model_id: int) -> tuple[str, ...]:
        return tuple(
            field.removesuffix("_model_id")
            for field, held in self.by_field.items()
            if held == model_id
        )


@dataclass(frozen=True)
class ExtractorEdit:
    name: str
    description: str
    schema: ExtractorSchema
    previous: ExtractorSchema
    roles: ModelRoles

    @property
    def added_columns(self) -> tuple[str, ...]:
        return tuple(name for name in self.schema.columns if name not in self.previous.columns)

    @property
    def removed_columns(self) -> tuple[str, ...]:
        return tuple(name for name in self.previous.columns if name not in self.schema.columns)


@dataclass(frozen=True)
class Extractor:
    id: int
    name: str
    description: str
    schema: ExtractorSchema
    source_columns: tuple[str, ...]
    roles: ModelRoles
    created_at: datetime
    updated_at: datetime

    def validated_source_values(self, values: Mapping[str, Any]) -> dict[str, str]:
        details: dict[str, str] = {}
        for name in self.source_columns:
            if name not in values:
                details[name] = "is required"
            elif not isinstance(values[name], str):
                details[name] = f"must be a string, not {type(values[name]).__name__}"
        for name in values:
            if name not in self.source_columns:
                details[name] = "is not a source column of this extractor"
        if details:
            raise ValidationError(details)
        return {name: values[name] for name in self.source_columns}

    def validated_row(self, values: Mapping[str, Any]) -> dict[str, Any]:
        source = {name: value for name, value in values.items() if name in self.source_columns}
        derived = {name: value for name, value in values.items() if name not in self.source_columns}
        return self.validated_source_values(source) | self.schema.derived_values(derived)


@dataclass(frozen=True)
class ExtractorDetail:
    extractor: Extractor
    datasets: tuple[Dataset, ...]
    models: tuple[Model, ...]
