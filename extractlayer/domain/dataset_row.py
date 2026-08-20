from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class RowSource(StrEnum):
    AI = "ai"
    HUMAN = "human"


@dataclass(frozen=True)
class DatasetRow:
    id: int
    dataset_id: int
    values: Mapping[str, Any]
    source: RowSource
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RowWrite:
    id: int | None
    dataset_id: int
    values: Mapping[str, Any]
    dead: bool
