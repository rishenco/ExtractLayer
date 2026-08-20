from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from extractlayer.domain.model import Model, ModelSpecification
from extractlayer.repo.pg.db import Pool

COLUMNS = "id, extractor_id, specification, known_datasets, archived_at, created_at, updated_at"

UNBOUND = (
    " AND NOT EXISTS (SELECT 1 FROM extractlayer.extractors AS e"
    " WHERE e.specimen_model_id = m.id OR e.serving_model_id = m.id)"
)


@dataclass(frozen=True)
class ModelRow:
    id: int
    extractor_id: int
    specification: dict[str, Any]
    known_datasets: list[int]
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def as_model(self) -> Model:
        return Model(
            id=self.id,
            extractor_id=self.extractor_id,
            specification=ModelSpecification(self.specification),
            known_datasets=tuple(self.known_datasets),
            archived_at=self.archived_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class PostgresModelRepo:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def create(
        self,
        extractor_id: int,
        specification: Mapping[str, Any],
        known_datasets: Sequence[int],
    ) -> Model:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(ModelRow))
            await cursor.execute(
                "INSERT INTO extractlayer.models (extractor_id, specification, known_datasets)"
                f" VALUES (%s, %s, %s) RETURNING {COLUMNS}",
                (extractor_id, Jsonb(specification), list(known_datasets)),
            )
            row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("the insert of a model returned no row")
        return row.as_model()

    async def get(self, model_id: int) -> Model | None:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(ModelRow))
            await cursor.execute(
                f"SELECT {COLUMNS} FROM extractlayer.models WHERE id = %s",
                (model_id,),
            )
            row = await cursor.fetchone()
        return None if row is None else row.as_model()

    async def live_for_extractor(self, extractor_id: int) -> list[Model]:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(ModelRow))
            await cursor.execute(
                f"SELECT {COLUMNS} FROM extractlayer.models"
                " WHERE extractor_id = %s AND archived_at IS NULL ORDER BY id",
                (extractor_id,),
            )
            rows = await cursor.fetchall()
        return [row.as_model() for row in rows]

    async def archive(self, model_id: int) -> Model | None:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(ModelRow))
            await cursor.execute(
                "UPDATE extractlayer.models AS m"
                " SET archived_at = coalesce(m.archived_at, now()), updated_at = now()"
                f" WHERE m.id = %s{UNBOUND} RETURNING {COLUMNS}",
                (model_id,),
            )
            row = await cursor.fetchone()
        return None if row is None else row.as_model()
