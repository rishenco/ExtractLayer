from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from extractlayer.domain.errors import (
    ConflictError,
    NotFoundError,
    UpstreamModelError,
    ValidationError,
)
from extractlayer.domain.extractor import ModelRoles
from extractlayer.domain.model import ModelKind, ModelSpecification
from extractlayer.domain.schema import ExtractorSchema
from extractlayer.repo.model_executors.dummy import DummyModelExecutor
from extractlayer.repo.pg.datasets import PostgresDatasetRepo
from extractlayer.repo.pg.extractors import PostgresExtractorRepo
from extractlayer.repo.pg.models import PostgresModelRepo
from extractlayer.service.extractors import ExtractorService
from extractlayer.service.models import ModelService

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"total": {"type": "number"}, "currency": {"type": "string"}},
}
SPECIFICATION: dict[str, Any] = {"kind": "dummy"}
SOURCE = {"body": "invoice 7", "subject": "October"}


class FixedExecutor:
    def __init__(self, produced: Mapping[str, Any]) -> None:
        self.produced = produced
        self.seen: list[Mapping[str, str]] = []

    async def run(
        self,
        _specification: ModelSpecification,
        _schema: ExtractorSchema,
        source_values: Mapping[str, str],
    ) -> Mapping[str, Any]:
        self.seen.append(source_values)
        return self.produced


def serving(
    extractors: PostgresExtractorRepo,
    models: PostgresModelRepo,
    datasets: PostgresDatasetRepo,
    executor: Any,
) -> ExtractorService:
    return ExtractorService(extractors, models, datasets, {ModelKind.DUMMY: executor})


async def test_the_dummy_kind_answers_null_for_every_column(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    extractor = await extractor_service.create("Invoices", "", SCHEMA, ["body", "subject"])
    model = await model_service.create(extractor.id, SPECIFICATION, [])
    await extractor_service.update(extractor.id, "Invoices", "", SCHEMA, ModelRoles(None, model.id))

    assert await extractor_service.serve(extractor.id, SOURCE) == {
        "total": None,
        "currency": None,
    }


async def test_serve_falls_back_to_the_specimen_when_no_serving_model_is_set(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    extractor = await extractor_service.create("Invoices", "", SCHEMA, ["body", "subject"])
    model = await model_service.create(extractor.id, SPECIFICATION, [])
    await extractor_service.update(extractor.id, "Invoices", "", SCHEMA, ModelRoles(model.id, None))

    assert await extractor_service.serve(extractor.id, SOURCE) == {
        "total": None,
        "currency": None,
    }


async def test_the_serving_model_is_preferred_over_the_specimen(
    extractors: PostgresExtractorRepo,
    models: PostgresModelRepo,
    datasets: PostgresDatasetRepo,
    extractor_service: ExtractorService,
    model_service: ModelService,
) -> None:
    extractor = await extractor_service.create("Invoices", "", SCHEMA, ["body", "subject"])
    specimen = await model_service.create(extractor.id, SPECIFICATION, [])
    serving_model = await model_service.create(extractor.id, {"kind": "dummy", "n": 2}, [])
    await extractor_service.update(
        extractor.id, "Invoices", "", SCHEMA, ModelRoles(specimen.id, serving_model.id)
    )

    executor = FixedExecutor({"total": 7, "currency": "EUR"})
    service = serving(extractors, models, datasets, executor)
    assert await service.serve(extractor.id, SOURCE) == {"total": 7, "currency": "EUR"}
    assert executor.seen == [SOURCE]


async def test_serving_with_neither_role_set_is_refused_by_name(
    extractor_service: ExtractorService,
) -> None:
    extractor = await extractor_service.create("Invoices", "", SCHEMA, ["body", "subject"])
    with pytest.raises(ConflictError) as raised:
        await extractor_service.serve(extractor.id, SOURCE)
    assert str(raised.value) == (
        f"extractor {extractor.id} names neither a serving nor a specimen model, so it cannot serve"
    )


async def test_serving_an_absent_extractor_raises_not_found(
    extractor_service: ExtractorService,
) -> None:
    with pytest.raises(NotFoundError) as raised:
        await extractor_service.serve(4321, SOURCE)
    assert raised.value.entity == "extractor"


async def test_a_source_row_that_does_not_fit_the_extractor_is_rejected_by_name(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    extractor = await extractor_service.create("Invoices", "", SCHEMA, ["body", "subject"])
    model = await model_service.create(extractor.id, SPECIFICATION, [])
    await extractor_service.update(extractor.id, "Invoices", "", SCHEMA, ModelRoles(None, model.id))

    with pytest.raises(ValidationError) as raised:
        await extractor_service.serve(extractor.id, {"body": "invoice 7"})
    assert raised.value.details == {"source_values.subject": "is required"}


async def test_a_model_returning_a_row_the_schema_rejects_is_an_upstream_failure(
    extractors: PostgresExtractorRepo,
    models: PostgresModelRepo,
    datasets: PostgresDatasetRepo,
    extractor_service: ExtractorService,
    model_service: ModelService,
) -> None:
    extractor = await extractor_service.create("Invoices", "", SCHEMA, ["body", "subject"])
    model = await model_service.create(extractor.id, SPECIFICATION, [])
    await extractor_service.update(extractor.id, "Invoices", "", SCHEMA, ModelRoles(None, model.id))

    service = serving(extractors, models, datasets, FixedExecutor({"total": "a lot"}))
    with pytest.raises(UpstreamModelError) as raised:
        await service.serve(extractor.id, SOURCE)
    assert f"model {model.id} returned a row extractor {extractor.id} rejects" in str(raised.value)


async def test_a_model_inventing_a_column_is_an_upstream_failure(
    extractors: PostgresExtractorRepo,
    models: PostgresModelRepo,
    datasets: PostgresDatasetRepo,
    extractor_service: ExtractorService,
    model_service: ModelService,
) -> None:
    extractor = await extractor_service.create("Invoices", "", SCHEMA, ["body", "subject"])
    model = await model_service.create(extractor.id, SPECIFICATION, [])
    await extractor_service.update(extractor.id, "Invoices", "", SCHEMA, ModelRoles(None, model.id))

    service = serving(extractors, models, datasets, FixedExecutor({"vat": 3}))
    with pytest.raises(UpstreamModelError):
        await service.serve(extractor.id, SOURCE)


async def test_the_dummy_executor_names_every_column_of_the_schema() -> None:
    produced = await DummyModelExecutor().run(
        ModelSpecification(SPECIFICATION), ExtractorSchema.parse(SCHEMA), {"body": "x"}
    )
    assert produced == {"total": None, "currency": None}
