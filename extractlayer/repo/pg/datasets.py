from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from psycopg.rows import class_row

from extractlayer.domain.dataset import Dataset
from extractlayer.repo.pg.db import Pool

COLUMNS = "id, extractor_id, name, description, created_at, updated_at"


@dataclass(frozen=True)
class DatasetRecord:
    id: int
    extractor_id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    def as_dataset(self) -> Dataset:
        return Dataset(
            id=self.id,
            extractor_id=self.extractor_id,
            name=self.name,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class PostgresDatasetRepo:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def create(self, extractor_id: int, name: str, description: str) -> Dataset:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(DatasetRecord))
            await cursor.execute(
                "INSERT INTO extractlayer.datasets (extractor_id, name, description)"
                f" VALUES (%s, %s, %s) RETURNING {COLUMNS}",
                (extractor_id, name, description),
            )
            row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("the insert of a dataset returned no row")
        return row.as_dataset()

    async def get(self, dataset_id: int) -> Dataset | None:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(DatasetRecord))
            await cursor.execute(
                f"SELECT {COLUMNS} FROM extractlayer.datasets WHERE id = %s",
                (dataset_id,),
            )
            row = await cursor.fetchone()
        return None if row is None else row.as_dataset()

    async def page(self, after_id: int | None, limit: int) -> list[Dataset]:
        where = "" if after_id is None else " WHERE id > %s"
        parameters: tuple[Any, ...] = (limit,) if after_id is None else (after_id, limit)
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(DatasetRecord))
            await cursor.execute(
                f"SELECT {COLUMNS} FROM extractlayer.datasets{where} ORDER BY id LIMIT %s",
                parameters,
            )
            rows = await cursor.fetchall()
        return [row.as_dataset() for row in rows]

    async def for_extractor(self, extractor_id: int) -> list[Dataset]:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(DatasetRecord))
            await cursor.execute(
                f"SELECT {COLUMNS} FROM extractlayer.datasets WHERE extractor_id = %s ORDER BY id",
                (extractor_id,),
            )
            rows = await cursor.fetchall()
        return [row.as_dataset() for row in rows]

    async def update(self, dataset_id: int, name: str, description: str) -> Dataset | None:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(DatasetRecord))
            await cursor.execute(
                "UPDATE extractlayer.datasets SET name = %s, description = %s, updated_at = now()"
                f" WHERE id = %s RETURNING {COLUMNS}",
                (name, description, dataset_id),
            )
            row = await cursor.fetchone()
        return None if row is None else row.as_dataset()
