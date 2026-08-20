from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from extractlayer.domain.errors import ValidationError


class ModelKind(StrEnum):
    DUMMY = "dummy"

    @classmethod
    def named(cls, value: object) -> ModelKind:
        for kind in cls:
            if kind.value == value:
                return kind
        known = ", ".join(repr(entry.value) for entry in cls)
        raise ValidationError(
            {"specification.kind": f"unknown model kind {value!r}; known kinds are {known}"}
        )


@dataclass(frozen=True)
class ModelSpecification:
    document: Mapping[str, Any]

    @classmethod
    def parse(cls, document: object) -> ModelSpecification:
        if not isinstance(document, Mapping):
            raise ValidationError(
                {"specification": f"must be a JSON object, not {type(document).__name__}"}
            )
        ModelKind.named(document.get("kind"))
        return cls(document)

    @property
    def kind(self) -> ModelKind:
        return ModelKind.named(self.document["kind"])


@dataclass(frozen=True)
class Model:
    id: int
    extractor_id: int
    specification: ModelSpecification
    known_datasets: tuple[int, ...]
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def kind(self) -> ModelKind:
        return self.specification.kind

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None
