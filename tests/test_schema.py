from typing import Any

import pytest

from extractlayer.domain.errors import ValidationError
from extractlayer.domain.schema import ExtractorSchema

INVOICE: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "total": {"type": "number", "x-el": {"metric": "exact"}},
        "lines": {
            "type": "array",
            "items": {"type": "string", "x-el": {"metric": "levenshtein"}},
            "x-el": {"metric": "unordered_array"},
        },
    },
}


def test_a_draft_2020_12_object_carrying_metric_config_is_accepted() -> None:
    schema = ExtractorSchema.parse(INVOICE)
    assert sorted(schema.columns) == ["lines", "total"]
    assert schema.columns["lines"]["items"]["x-el"] == {"metric": "levenshtein"}


@pytest.mark.parametrize("document", ["a string", 7, ["a", "list"], None])
def test_a_non_object_schema_is_rejected_by_name(document: object) -> None:
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.parse(document)
    assert "schema" in raised.value.details
    assert "must be a JSON object" in raised.value.details["schema"]


def test_a_schema_that_is_not_an_object_type_is_rejected_by_name() -> None:
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.parse({"type": "array", "items": {"type": "string"}})
    assert raised.value.details["schema.type"] == 'must be "object"'


@pytest.mark.parametrize("document", [{"type": "object"}, {"type": "object", "properties": {}}])
def test_an_object_with_no_properties_is_rejected_by_name(document: dict[str, Any]) -> None:
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.parse(document)
    assert raised.value.details["schema.properties"] == "must declare at least one column"


def test_an_unknown_metric_key_is_rejected_by_name() -> None:
    document = {
        "type": "object",
        "properties": {"total": {"type": "number", "x-el": {"metric": "exact", "weight": 2}}},
    }
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.parse(document)
    assert raised.value.details["schema.properties.total.x-el"] == "unknown x-el key 'weight'"


def test_an_unknown_metric_key_on_array_items_is_rejected_by_name() -> None:
    document = {
        "type": "object",
        "properties": {
            "lines": {"type": "array", "items": {"type": "string", "x-el": {"threshold": 0.5}}}
        },
    }
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.parse(document)
    assert (
        raised.value.details["schema.properties.lines.items.x-el"]
        == "unknown x-el key 'threshold'"
    )


def test_an_invalid_draft_2020_12_schema_is_rejected() -> None:
    document = {"type": "object", "properties": {"total": {"type": "number", "minimum": "high"}}}
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.parse(document)
    assert "schema" in raised.value.details


def test_an_edit_changing_a_column_type_is_refused() -> None:
    previous = ExtractorSchema.parse(INVOICE)
    document = {
        "type": "object",
        "properties": {
            "total": {"type": "string"},
            "lines": {"type": "array", "items": {"type": "string"}},
        },
    }
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.edited(previous, document)
    assert "cannot change from 'number' to 'string'" in (
        raised.value.details["schema.properties.total.type"]
    )


def test_an_edit_adding_and_removing_columns_succeeds() -> None:
    previous = ExtractorSchema.parse(INVOICE)
    document = {
        "type": "object",
        "properties": {
            "total": {"type": "number", "x-el": {"metric": "exact"}},
            "currency": {"type": "string"},
        },
    }
    edited = ExtractorSchema.edited(previous, document)
    assert sorted(edited.columns) == ["currency", "total"]


def test_an_edit_is_validated_like_a_new_schema() -> None:
    previous = ExtractorSchema.parse(INVOICE)
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.edited(previous, {"type": "object", "properties": {}})
    assert raised.value.details["schema.properties"] == "must declare at least one column"
