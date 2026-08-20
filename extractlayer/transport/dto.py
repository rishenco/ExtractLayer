from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from extractlayer.domain.dataset import Dataset
from extractlayer.domain.dataset_row import DatasetRow, RowSource, RowWrite
from extractlayer.domain.extractor import Extractor, ExtractorDetail
from extractlayer.domain.model import Model


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
    specimen_model_id: int | None
    serving_model_id: int | None


class ExtractorView(BaseModel):
    id: int
    name: str
    description: str
    document: dict[str, Any] = Field(serialization_alias="schema")
    source_columns: list[str]
    specimen_model_id: int | None
    serving_model_id: int | None
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
            specimen_model_id=extractor.roles.specimen_model_id,
            serving_model_id=extractor.roles.serving_model_id,
            created_at=extractor.created_at,
            updated_at=extractor.updated_at,
        )


class ExtractorDatasetView(BaseModel):
    id: int
    name: str
    description: str

    @classmethod
    def of(cls, dataset: Dataset) -> ExtractorDatasetView:
        return cls(id=dataset.id, name=dataset.name, description=dataset.description)


class ExtractorModelView(BaseModel):
    id: int
    kind: str
    known_datasets: list[int]

    @classmethod
    def of(cls, model: Model) -> ExtractorModelView:
        return cls(
            id=model.id,
            kind=model.kind.value,
            known_datasets=list(model.known_datasets),
        )


class ExtractorDetailView(ExtractorView):
    datasets: list[ExtractorDatasetView]
    models: list[ExtractorModelView]

    @classmethod
    def of_detail(cls, detail: ExtractorDetail) -> ExtractorDetailView:
        return cls(
            **ExtractorView.of(detail.extractor).model_dump(),
            datasets=[ExtractorDatasetView.of(dataset) for dataset in detail.datasets],
            models=[ExtractorModelView.of(model) for model in detail.models],
        )


class ServeRequest(Payload):
    source_values: dict[str, Any]


class ServeView(BaseModel):
    derived_values: dict[str, Any]


class ModelCreate(Payload):
    extractor_id: int
    specification: dict[str, Any]
    known_datasets: list[int]


class ModelView(BaseModel):
    id: int
    extractor_id: int
    specification: dict[str, Any]
    known_datasets: list[int]
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, model: Model) -> ModelView:
        return cls(
            id=model.id,
            extractor_id=model.extractor_id,
            specification=dict(model.specification.document),
            known_datasets=list(model.known_datasets),
            archived_at=model.archived_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class DatasetCreate(Payload):
    extractor_id: int
    name: str
    description: str


class DatasetUpdate(Payload):
    name: str
    description: str


class DatasetView(BaseModel):
    id: int
    extractor_id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, dataset: Dataset) -> DatasetView:
        return cls(
            id=dataset.id,
            extractor_id=dataset.extractor_id,
            name=dataset.name,
            description=dataset.description,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )


class RowPayload(Payload):
    id: int | None
    dataset_id: int
    values: dict[str, Any]
    dead: bool

    def as_write(self) -> RowWrite:
        return RowWrite(
            id=self.id,
            dataset_id=self.dataset_id,
            values=self.values,
            dead=self.dead,
        )


class RowBatch(Payload):
    rows: list[RowPayload]


class RowView(BaseModel):
    id: int
    dataset_id: int
    values: dict[str, Any]
    source: RowSource
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, row: DatasetRow) -> RowView:
        return cls(
            id=row.id,
            dataset_id=row.dataset_id,
            values=dict(row.values),
            source=row.source,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
