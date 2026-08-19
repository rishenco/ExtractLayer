from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import TupleRow
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from extractlayer.domain.extractor import Extractor
from extractlayer.domain.schema import ExtractorSchema

COLUMNS = "id, name, description, schema, source_columns, created_at, updated_at"


def as_extractor(row: Sequence[Any]) -> Extractor:
    return Extractor(
        id=row[0],
        name=row[1],
        description=row[2],
        schema=ExtractorSchema(row[3]),
        source_columns=tuple(row[4]),
        created_at=row[5],
        updated_at=row[6],
    )


class PostgresExtractorRepo:
    def __init__(self, pool: AsyncConnectionPool[AsyncConnection[TupleRow]]) -> None:
        self.pool = pool

    async def create(
        self,
        name: str,
        description: str,
        schema: Mapping[str, Any],
        source_columns: Sequence[str],
    ) -> Extractor:
        async with self.pool.connection() as connection:
            cursor = await connection.execute(
                f"INSERT INTO extractlayer.extractors (name, description, schema, source_columns)"
                f" VALUES (%s, %s, %s, %s) RETURNING {COLUMNS}",
                (name, description, Jsonb(schema), list(source_columns)),
            )
            row = await cursor.fetchone()
        assert row is not None
        return as_extractor(row)

    async def get(self, extractor_id: int) -> Extractor | None:
        async with self.pool.connection() as connection:
            cursor = await connection.execute(
                f"SELECT {COLUMNS} FROM extractlayer.extractors WHERE id = %s",
                (extractor_id,),
            )
            row = await cursor.fetchone()
        return None if row is None else as_extractor(row)

    async def page(self, after_id: int | None, limit: int) -> list[Extractor]:
        where = "" if after_id is None else " WHERE id > %s"
        parameters: tuple[Any, ...] = (limit,) if after_id is None else (after_id, limit)
        async with self.pool.connection() as connection:
            cursor = await connection.execute(
                f"SELECT {COLUMNS} FROM extractlayer.extractors{where} ORDER BY id LIMIT %s",
                parameters,
            )
            rows = await cursor.fetchall()
        return [as_extractor(row) for row in rows]

    async def update(
        self,
        extractor_id: int,
        name: str,
        description: str,
        schema: Mapping[str, Any],
    ) -> Extractor | None:
        async with self.pool.connection() as connection:
            cursor = await connection.execute(
                "UPDATE extractlayer.extractors"
                " SET name = %s, description = %s, schema = %s, updated_at = now()"
                f" WHERE id = %s RETURNING {COLUMNS}",
                (name, description, Jsonb(schema), extractor_id),
            )
            row = await cursor.fetchone()
        return None if row is None else as_extractor(row)

    async def delete(self, extractor_id: int) -> bool:
        async with self.pool.connection() as connection:
            cursor = await connection.execute(
                "DELETE FROM extractlayer.extractors WHERE id = %s",
                (extractor_id,),
            )
            return cursor.rowcount > 0
