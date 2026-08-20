from __future__ import annotations

from typing import Any

import pytest

from extractlayer.domain.errors import ConflictError, NotFoundError, ValidationError
from extractlayer.domain.extractor import ModelRoles
from extractlayer.domain.model import ModelKind
from extractlayer.service.datasets import DatasetService
from extractlayer.service.extractors import ExtractorService
from extractlayer.service.models import ModelService

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
SPECIFICATION: dict[str, Any] = {"kind": "dummy", "prompt": "read the invoice"}
ABSENT = 4321


async def test_a_model_round_trips_through_the_service(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    created = await model_service.create(extractor.id, SPECIFICATION, [7])
    read = await model_service.get(created.id)
    assert read == created
    assert read.kind is ModelKind.DUMMY
    assert read.known_datasets == (7,)


async def test_a_model_of_an_absent_extractor_is_not_created(
    model_service: ModelService,
) -> None:
    with pytest.raises(NotFoundError) as raised:
        await model_service.create(ABSENT, SPECIFICATION, [])
    assert raised.value.entity == "extractor"


async def test_a_specification_naming_an_unknown_kind_is_rejected_by_name(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    with pytest.raises(ValidationError) as raised:
        await model_service.create(extractor.id, {"kind": "psychic"}, [])
    assert raised.value.details["specification.kind"] == (
        "unknown model kind 'psychic'; known kinds are 'dummy'"
    )


async def test_a_specification_naming_no_kind_is_rejected_by_name(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    with pytest.raises(ValidationError) as raised:
        await model_service.create(extractor.id, {"prompt": "read it"}, [])
    assert "specification.kind" in raised.value.details


async def test_reading_an_absent_model_raises_not_found(model_service: ModelService) -> None:
    with pytest.raises(NotFoundError) as raised:
        await model_service.get(ABSENT)
    assert raised.value.entity == "model"


async def test_an_archived_model_still_reads(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    created = await model_service.create(extractor.id, SPECIFICATION, [])
    archived = await model_service.archive(created.id)
    assert archived.is_archived is True
    assert (await model_service.get(created.id)).is_archived is True


async def test_archiving_an_absent_model_raises_not_found(model_service: ModelService) -> None:
    with pytest.raises(NotFoundError):
        await model_service.archive(ABSENT)


async def test_a_model_a_role_names_cannot_be_archived(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    model = await model_service.create(extractor.id, SPECIFICATION, [])
    await extractor_service.update(
        extractor.id,
        "Invoices",
        "line items",
        SCHEMA,
        ModelRoles(specimen_model_id=None, serving_model_id=model.id),
    )

    with pytest.raises(ConflictError) as raised:
        await model_service.archive(model.id)
    assert str(raised.value) == (
        f"model {model.id} is the serving model of extractor {extractor.id},"
        " so it cannot be archived"
    )
    assert (await model_service.get(model.id)).is_archived is False


async def test_an_archived_model_cannot_be_set_as_a_role(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    model = await model_service.create(extractor.id, SPECIFICATION, [])
    await model_service.archive(model.id)

    with pytest.raises(ValidationError) as raised:
        await extractor_service.update(
            extractor.id,
            "Invoices",
            "line items",
            SCHEMA,
            ModelRoles(specimen_model_id=model.id, serving_model_id=None),
        )
    assert raised.value.details["specimen_model_id"] == "names an archived model"


async def test_a_role_naming_another_extractors_model_is_rejected_by_name(
    extractor_service: ExtractorService, model_service: ModelService
) -> None:
    mine = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    theirs = await extractor_service.create("Receipts", "totals", SCHEMA, ["body"])
    model = await model_service.create(theirs.id, SPECIFICATION, [])

    with pytest.raises(ValidationError) as raised:
        await extractor_service.update(
            mine.id,
            "Invoices",
            "line items",
            SCHEMA,
            ModelRoles(specimen_model_id=None, serving_model_id=model.id),
        )
    assert raised.value.details["serving_model_id"] == f"names a model of extractor {theirs.id}"


async def test_a_role_naming_no_model_is_rejected_by_name(
    extractor_service: ExtractorService,
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    with pytest.raises(ValidationError) as raised:
        await extractor_service.update(
            extractor.id,
            "Invoices",
            "line items",
            SCHEMA,
            ModelRoles(specimen_model_id=ABSENT, serving_model_id=None),
        )
    assert "names no model" in raised.value.details["specimen_model_id"]


async def test_an_extractor_carries_its_datasets_and_its_live_models(
    extractor_service: ExtractorService,
    model_service: ModelService,
    dataset_service: DatasetService,
) -> None:
    extractor = await extractor_service.create("Invoices", "line items", SCHEMA, ["body"])
    dataset = await dataset_service.create(extractor.id, "Golden", "hand checked")
    kept = await model_service.create(extractor.id, SPECIFICATION, [dataset.id])
    hidden = await model_service.create(extractor.id, SPECIFICATION, [])
    await model_service.archive(hidden.id)

    detail = await extractor_service.detail(extractor.id)
    assert detail.extractor.id == extractor.id
    assert [(d.id, d.name, d.description) for d in detail.datasets] == [
        (dataset.id, "Golden", "hand checked")
    ]
    assert [(m.id, m.kind, m.known_datasets) for m in detail.models] == [
        (kept.id, ModelKind.DUMMY, (dataset.id,))
    ]
