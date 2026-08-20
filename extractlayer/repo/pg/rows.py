from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from extractlayer.domain.dataset_row import DatasetRow, RowSource, RowWrite
from extractlayer.repo.pg.db import Pool

COLUMNS = 'id, dataset_id, "values", source, created_at, updated_at'
ALIASED = 'r.id, r.dataset_id, r."values", r.source, r.created_at, r.updated_at'

INSERT_ROWS = (
    'INSERT INTO extractlayer.dataset_rows (dataset_id, "values", source)'
    " SELECT * FROM unnest(%s::integer[], %s::jsonb[], %s::text[])"
    f" RETURNING {COLUMNS}"
)

UPDATE_ROWS = (
    'UPDATE extractlayer.dataset_rows AS r SET "values" = u.document, source = u.source,'
    " updated_at = now()"
    " FROM unnest(%s::integer[], %s::jsonb[], %s::text[], %s::integer[])"
    " AS u(id, document, source, dataset_id)"
    f" WHERE r.id = u.id AND r.dataset_id = u.dataset_id RETURNING {ALIASED}"
)


@dataclass(frozen=True)
class RowRecord:
    id: int
    dataset_id: int
    values: dict[str, Any]
    source: str
    created_at: datetime
    updated_at: datetime

    def as_row(self) -> DatasetRow:
        return DatasetRow(
            id=self.id,
            dataset_id=self.dataset_id,
            values=self.values,
            source=RowSource(self.source),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class PostgresRowRepo:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def page(self, dataset_id: int, after_id: int | None, limit: int) -> list[DatasetRow]:
        after = "" if after_id is None else " AND id > %s"
        parameters: tuple[Any, ...] = (
            (dataset_id, limit) if after_id is None else (dataset_id, after_id, limit)
        )
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(RowRecord))
            await cursor.execute(
                f"SELECT {COLUMNS} FROM extractlayer.dataset_rows"
                f" WHERE dataset_id = %s{after} ORDER BY id LIMIT %s",
                parameters,
            )
            rows = await cursor.fetchall()
        return [row.as_row() for row in rows]

    async def datasets_of(self, row_ids: Sequence[int]) -> dict[int, int]:
        if not row_ids:
            return {}
        async with self.pool.connection() as connection:
            cursor = await connection.execute(
                "SELECT id, dataset_id FROM extractlayer.dataset_rows WHERE id = ANY(%s)",
                (list(row_ids),),
            )
            found = await cursor.fetchall()
        return {row[0]: row[1] for row in found}

    async def apply(self, writes: Sequence[RowWrite], source: RowSource) -> list[DatasetRow]:
        dead = [write.id for write in writes if write.dead]
        updates = [write for write in writes if not write.dead and write.id is not None]
        inserts = [write for write in writes if not write.dead and write.id is None]
        landed: list[DatasetRow] = []
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(RowRecord))
            if dead:
                await cursor.execute(
                    "DELETE FROM extractlayer.dataset_rows WHERE id = ANY(%s)",
                    (dead,),
                )
            if updates:
                await cursor.execute(
                    UPDATE_ROWS,
                    (
                        [write.id for write in updates],
                        [Jsonb(write.values) for write in updates],
                        [source.value] * len(updates),
                        [write.dataset_id for write in updates],
                    ),
                )
                landed.extend(row.as_row() for row in await cursor.fetchall())
            if inserts:
                await cursor.execute(
                    INSERT_ROWS,
                    (
                        [write.dataset_id for write in inserts],
                        [Jsonb(write.values) for write in inserts],
                        [source.value] * len(inserts),
                    ),
                )
                landed.extend(row.as_row() for row in await cursor.fetchall())
        return sorted(landed, key=lambda row: row.id)
