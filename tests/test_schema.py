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
    assert raised.value.details["schema.properties.total.type"] == (
        'cannot change from {"type": "number"} to {"type": "string"};'
        " a schema edit adds and removes columns only"
    )


def test_an_edit_changing_an_array_column_element_type_is_refused() -> None:
    previous = ExtractorSchema.parse(INVOICE)
    document = {
        "type": "object",
        "properties": {
            "total": {"type": "number"},
            "lines": {"type": "array", "items": {"type": "number"}},
        },
    }
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.edited(previous, document)
    assert "schema.properties.lines.type" in raised.value.details


def test_an_edit_changing_a_nested_property_type_is_refused() -> None:
    previous = ExtractorSchema.parse(
        {
            "type": "object",
            "properties": {
                "seller": {"type": "object", "properties": {"vat": {"type": "string"}}}
            },
        }
    )
    document = {
        "type": "object",
        "properties": {"seller": {"type": "object", "properties": {"vat": {"type": "number"}}}},
    }
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.edited(previous, document)
    assert "schema.properties.seller.type" in raised.value.details


def test_an_edit_changing_the_value_type_of_an_enum_column_is_refused() -> None:
    previous = ExtractorSchema.parse(
        {"type": "object", "properties": {"status": {"enum": ["draft", "sent"]}}}
    )
    document = {"type": "object", "properties": {"status": {"enum": [1, 2]}}}
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.edited(previous, document)
    assert "schema.properties.status.type" in raised.value.details


def test_an_edit_widening_an_enum_within_one_value_type_succeeds() -> None:
    previous = ExtractorSchema.parse(
        {"type": "object", "properties": {"status": {"enum": ["draft", "sent"]}}}
    )
    document = {"type": "object", "properties": {"status": {"enum": ["draft", "sent", "void"]}}}
    assert ExtractorSchema.edited(previous, document).columns["status"]["enum"] == [
        "draft",
        "sent",
        "void",
    ]


def test_a_single_entry_type_list_is_the_same_type_as_the_bare_name() -> None:
    previous = ExtractorSchema.parse(
        {"type": "object", "properties": {"total": {"type": ["number"]}}}
    )
    document = {"type": "object", "properties": {"total": {"type": "number"}}}
    assert ExtractorSchema.edited(previous, document).columns["total"]["type"] == "number"


def test_a_refused_multi_type_change_reports_json_not_a_python_tuple() -> None:
    previous = ExtractorSchema.parse(
        {"type": "object", "properties": {"total": {"type": ["string", "null"]}}}
    )
    document = {"type": "object", "properties": {"total": {"type": "number"}}}
    with pytest.raises(ValidationError) as raised:
        ExtractorSchema.edited(previous, document)
    message = raised.value.details["schema.properties.total.type"]
    assert 'cannot change from {"type": ["null", "string"]} to {"type": "number"}' in message
    assert "(" not in message


def test_an_edit_changing_only_metric_config_and_description_succeeds() -> None:
    previous = ExtractorSchema.parse(INVOICE)
    document = {
        "type": "object",
        "properties": {
            "total": {"type": "number", "description": "gross", "x-el": {"metric": "exact"}},
            "lines": {
                "type": "array",
                "items": {"type": "string", "x-el": {"metric": "exact"}},
                "x-el": {"metric": "ordered_array"},
            },
        },
    }
    edited = ExtractorSchema.edited(previous, document)
    assert edited.columns["lines"]["x-el"] == {"metric": "ordered_array"}


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
