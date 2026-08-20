from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from extractlayer.domain.errors import ValidationError
from extractlayer.domain.extractor import Extractor, ModelRoles
from extractlayer.domain.schema import ExtractorSchema

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"total": {"type": "number"}, "currency": {"type": "string"}},
    "required": ["total"],
}


def extractor(schema: dict[str, Any] | None = None) -> Extractor:
    at = datetime(2026, 1, 1, tzinfo=UTC)
    return Extractor(
        id=1,
        name="Invoices",
        description="line items",
        schema=ExtractorSchema.parse(schema or SCHEMA),
        source_columns=("body", "subject"),
        roles=ModelRoles(specimen_model_id=None, serving_model_id=None),
        created_at=at,
        updated_at=at,
    )


def test_a_row_carrying_every_column_round_trips() -> None:
    values = {"body": "hi", "subject": "invoice", "total": 12, "currency": "EUR"}
    assert extractor().validated_row(values) == values


def test_a_missing_source_value_is_rejected_by_name() -> None:
    with pytest.raises(ValidationError) as raised:
        extractor().validated_row({"subject": "invoice", "total": 12})
    assert raised.value.details == {"body": "is required"}


def test_a_source_value_that_is_not_a_string_is_rejected_by_name() -> None:
    with pytest.raises(ValidationError) as raised:
        extractor().validated_row({"body": 7, "subject": "invoice"})
    assert raised.value.details["body"] == "must be a string, not int"


def test_a_value_naming_no_column_is_rejected_by_name() -> None:
    with pytest.raises(ValidationError) as raised:
        extractor().validated_row({"body": "hi", "subject": "invoice", "vat": 1})
    assert raised.value.details == {"vat": "is not a column of this extractor's schema"}


def test_a_source_value_that_is_not_a_source_column_is_rejected_by_name() -> None:
    with pytest.raises(ValidationError) as raised:
        extractor().validated_source_values({"body": "hi", "subject": "s", "sender": "a@b"})
    assert raised.value.details == {"sender": "is not a source column of this extractor"}


def test_a_derived_column_may_be_null_even_when_the_schema_requires_it() -> None:
    row = extractor().validated_row({"body": "hi", "subject": "invoice", "total": None})
    assert row["total"] is None


def test_a_missing_derived_column_normalizes_to_null() -> None:
    row = extractor().validated_row({"body": "hi", "subject": "invoice", "total": 12})
    assert row == {"body": "hi", "subject": "invoice", "total": 12, "currency": None}


def test_a_derived_value_of_the_wrong_type_is_rejected_by_column_name() -> None:
    with pytest.raises(ValidationError) as raised:
        extractor().validated_row({"body": "hi", "subject": "s", "total": "twelve"})
    assert "total" in raised.value.details


def test_a_nested_derived_value_is_rejected_by_its_path() -> None:
    nested: dict[str, Any] = {
        "type": "object",
        "properties": {
            "seller": {"type": "object", "properties": {"vat": {"type": "string"}}},
        },
    }
    with pytest.raises(ValidationError) as raised:
        extractor(nested).validated_row({"body": "hi", "subject": "s", "seller": {"vat": 7}})
    assert "seller.vat" in raised.value.details


def test_a_derived_column_defined_through_a_reference_is_validated() -> None:
    referenced: dict[str, Any] = {
        "type": "object",
        "$defs": {"money": {"type": "number"}},
        "properties": {"total": {"$ref": "#/$defs/money"}},
    }
    with pytest.raises(ValidationError) as raised:
        extractor(referenced).validated_row({"body": "hi", "subject": "s", "total": "twelve"})
    assert "total" in raised.value.details


def test_details_take_the_prefix_of_the_field_that_carried_them() -> None:
    with pytest.raises(ValidationError) as raised:
        extractor().validated_row({"subject": "invoice"})
    assert raised.value.at("rows.3.values").details == {"rows.3.values.body": "is required"}
