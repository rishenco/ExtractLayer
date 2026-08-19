from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from jsonschema.exceptions import SchemaError
from jsonschema.validators import Draft202012Validator

from extractlayer.domain.errors import ValidationError

METRIC_KEYWORD = "x-el"
METRIC_KEYS = frozenset({"metric"})


def _type_of(column: Mapping[str, Any]) -> Any:
    declared = column.get("type")
    if isinstance(declared, list):
        return tuple(sorted(str(entry) for entry in declared))
    return declared


def _metric_details(path: str, config: Any) -> dict[str, str]:
    if not isinstance(config, Mapping):
        return {path: f"{METRIC_KEYWORD} must be an object, not {type(config).__name__}"}
    unknown = sorted(str(key) for key in config if key not in METRIC_KEYS)
    if unknown:
        return {path: f"unknown {METRIC_KEYWORD} key {unknown[0]!r}"}
    return {}


@dataclass(frozen=True)
class ExtractorSchema:
    document: Mapping[str, Any]

    @classmethod
    def parse(cls, document: object) -> ExtractorSchema:
        if not isinstance(document, Mapping):
            raise ValidationError(
                {"schema": f"must be a JSON object, not {type(document).__name__}"}
            )
        if document.get("type") != "object":
            raise ValidationError({"schema.type": 'must be "object"'})

        properties = document.get("properties")
        if not isinstance(properties, Mapping) or not properties:
            raise ValidationError({"schema.properties": "must declare at least one column"})

        try:
            Draft202012Validator.check_schema(dict(document))
        except SchemaError as error:
            raise ValidationError({"schema": error.message}) from error

        details: dict[str, str] = {}
        for name, column in properties.items():
            if not isinstance(column, Mapping):
                details[f"schema.properties.{name}"] = (
                    f"must be a JSON object, not {type(column).__name__}"
                )
                continue
            if METRIC_KEYWORD in column:
                details |= _metric_details(
                    f"schema.properties.{name}.{METRIC_KEYWORD}", column[METRIC_KEYWORD]
                )
            items = column.get("items")
            if isinstance(items, Mapping) and METRIC_KEYWORD in items:
                details |= _metric_details(
                    f"schema.properties.{name}.items.{METRIC_KEYWORD}", items[METRIC_KEYWORD]
                )
        if details:
            raise ValidationError(details)

        return cls(document)

    @classmethod
    def edited(cls, previous: ExtractorSchema, document: object) -> ExtractorSchema:
        edited = cls.parse(document)
        details: dict[str, str] = {}
        for name, column in edited.columns.items():
            kept = previous.columns.get(name)
            if kept is None:
                continue
            before, after = _type_of(kept), _type_of(column)
            if before != after:
                details[f"schema.properties.{name}.type"] = (
                    f"cannot change from {before!r} to {after!r};"
                    " a schema edit adds and removes columns only"
                )
        if details:
            raise ValidationError(details)
        return edited

    @property
    def columns(self) -> Mapping[str, Mapping[str, Any]]:
        return dict(self.document["properties"])
