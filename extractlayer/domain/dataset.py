from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Dataset:
    id: int
    extractor_id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
