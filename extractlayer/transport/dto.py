from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from extractlayer.domain.extractor import Extractor


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExtractorCreate(Payload):
    name: str
    description: str
    document: dict[str, Any] = Field(alias="schema")
    source_columns: list[str]


class ExtractorUpdate(Payload):
    name: str
    description: str
    document: dict[str, Any] = Field(alias="schema")


class ExtractorView(BaseModel):
    id: int
    name: str
    description: str
    document: dict[str, Any] = Field(serialization_alias="schema")
    source_columns: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, extractor: Extractor) -> ExtractorView:
        return cls(
            id=extractor.id,
            name=extractor.name,
            description=extractor.description,
            document=dict(extractor.schema.document),
            source_columns=list(extractor.source_columns),
            created_at=extractor.created_at,
            updated_at=extractor.updated_at,
        )
