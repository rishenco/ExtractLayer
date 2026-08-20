from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from extractlayer.domain.model import ModelSpecification
from extractlayer.domain.schema import ExtractorSchema


class DummyModelExecutor:
    async def run(
        self,
        _specification: ModelSpecification,
        schema: ExtractorSchema,
        _source_values: Mapping[str, str],
    ) -> Mapping[str, Any]:
        return dict.fromkeys(schema.columns)
