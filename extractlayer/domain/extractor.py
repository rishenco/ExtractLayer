from dataclasses import dataclass
from datetime import datetime

from extractlayer.domain.schema import ExtractorSchema


@dataclass(frozen=True)
class Extractor:
    id: int
    name: str
    description: str
    schema: ExtractorSchema
    source_columns: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
