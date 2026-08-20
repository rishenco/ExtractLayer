from __future__ import annotations

from typing import Any

import pytest

from extractlayer.domain.errors import NotFoundError, ValidationError
from extractlayer.domain.extractor import ModelRoles
from extractlayer.service.extractors import ExtractorService

SCHEMA: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "number"}}}
ABSENT = 4321
NO_ROLES = ModelRoles(specimen_model_id=None, serving_model_id=None)


@pytest.fixture
def service(extractor_service: ExtractorService) -> ExtractorService:
    return extractor_service


async def test_a_created_extractor_carries_its_validated_schema(
    service: ExtractorService,
) -> None:
    created = await service.create("Invoices", "line items", SCHEMA, ["body"])
    assert (await service.get(created.id)).schema.document == SCHEMA


async def test_creating_with_an_invalid_schema_raises_a_domain_validation_error(
    service: ExtractorService,
) -> None:
    with pytest.raises(ValidationError) as raised:
        await service.create("Invoices", "line items", {"type": "object"}, ["body"])
    assert raised.value.details["schema.properties"] == "must declare at least one column"


async def test_reading_an_absent_extractor_raises_not_found(service: ExtractorService) -> None:
    with pytest.raises(NotFoundError) as raised:
        await service.get(ABSENT)
    assert raised.value.entity == "extractor"
    assert raised.value.entity_id == ABSENT


async def test_deleting_an_absent_extractor_raises_not_found(service: ExtractorService) -> None:
    with pytest.raises(NotFoundError):
        await service.delete(ABSENT)


async def test_updating_an_absent_extractor_raises_not_found(service: ExtractorService) -> None:
    with pytest.raises(NotFoundError):
        await service.update(ABSENT, "Receipts", "totals", SCHEMA, NO_ROLES)


async def test_an_update_leaves_source_columns_as_created(service: ExtractorService) -> None:
    created = await service.create("Invoices", "line items", SCHEMA, ["body", "subject"])
    updated = await service.update(created.id, "Receipts", "totals", SCHEMA, NO_ROLES)
    assert updated.source_columns == ("body", "subject")


async def test_an_update_changing_a_column_type_is_refused(service: ExtractorService) -> None:
    created = await service.create("Invoices", "line items", SCHEMA, ["body"])
    changed: dict[str, Any] = {"type": "object", "properties": {"total": {"type": "string"}}}
    with pytest.raises(ValidationError) as raised:
        await service.update(created.id, "Invoices", "line items", changed, NO_ROLES)
    assert 'cannot change from {"type": "number"} to {"type": "string"}' in (
        raised.value.details["schema.properties.total.type"]
    )
    assert (await service.get(created.id)).schema.document == SCHEMA


async def test_an_update_adding_and_removing_columns_succeeds(service: ExtractorService) -> None:
    created = await service.create("Invoices", "line items", SCHEMA, ["body"])
    edited: dict[str, Any] = {
        "type": "object",
        "properties": {"total": {"type": "number"}, "currency": {"type": "string"}},
    }
    updated = await service.update(created.id, "Invoices", "line items", edited, NO_ROLES)
    assert sorted(updated.schema.columns) == ["currency", "total"]


async def test_a_cursor_walks_the_service_listing_once(service: ExtractorService) -> None:
    seeded = [
        (await service.create(f"Extractor {index}", "", SCHEMA, ["body"])).id
        for index in range(5)
    ]

    walked: list[int] = []
    after_id: int | None = None
    while page := await service.page(after_id, 2):
        walked.extend(extractor.id for extractor in page)
        after_id = page[-1].id

    assert walked == seeded
