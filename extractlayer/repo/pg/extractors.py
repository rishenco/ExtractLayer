from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from extractlayer.domain.extractor import Extractor, ExtractorEdit, ModelRoles
from extractlayer.domain.schema import ExtractorSchema
from extractlayer.repo.pg.db import Pool

COLUMNS = (
    "id, name, description, schema, source_columns,"
    " specimen_model_id, serving_model_id, created_at, updated_at"
)

REWRITE_ROWS = (
    'UPDATE extractlayer.dataset_rows AS r SET "values" = (r."values" - %s::text[]) || %s::jsonb,'
    " updated_at = now() FROM extractlayer.datasets AS d"
    " WHERE d.id = r.dataset_id AND d.extractor_id = %s"
)


@dataclass(frozen=True)
class ExtractorRow:
    id: int
    name: str
    description: str
    schema: dict[str, Any]
    source_columns: list[str]
    specimen_model_id: int | None
    serving_model_id: int | None
    created_at: datetime
    updated_at: datetime

    def as_extractor(self) -> Extractor:
        return Extractor(
            id=self.id,
            name=self.name,
            description=self.description,
            schema=ExtractorSchema(self.schema),
            source_columns=tuple(self.source_columns),
            roles=ModelRoles(
                specimen_model_id=self.specimen_model_id,
                serving_model_id=self.serving_model_id,
            ),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class PostgresExtractorRepo:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def create(
        self,
        name: str,
        description: str,
        schema: Mapping[str, Any],
        source_columns: Sequence[str],
    ) -> Extractor:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(ExtractorRow))
            await cursor.execute(
                f"INSERT INTO extractlayer.extractors (name, description, schema, source_columns)"
                f" VALUES (%s, %s, %s, %s) RETURNING {COLUMNS}",
                (name, description, Jsonb(schema), list(source_columns)),
            )
            row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("the insert of an extractor returned no row")
        return row.as_extractor()

    async def get(self, extractor_id: int) -> Extractor | None:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(ExtractorRow))
            await cursor.execute(
                f"SELECT {COLUMNS} FROM extractlayer.extractors WHERE id = %s",
                (extractor_id,),
            )
            row = await cursor.fetchone()
        return None if row is None else row.as_extractor()

    async def page(self, after_id: int | None, limit: int) -> list[Extractor]:
        where = "" if after_id is None else " WHERE id > %s"
        parameters: tuple[Any, ...] = (limit,) if after_id is None else (after_id, limit)
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(ExtractorRow))
            await cursor.execute(
                f"SELECT {COLUMNS} FROM extractlayer.extractors{where} ORDER BY id LIMIT %s",
                parameters,
            )
            rows = await cursor.fetchall()
        return [row.as_extractor() for row in rows]

    async def update(self, extractor_id: int, edit: ExtractorEdit) -> Extractor | None:
        async with self.pool.connection() as connection:
            cursor = connection.cursor(row_factory=class_row(ExtractorRow))
            await cursor.execute(
                "UPDATE extractlayer.extractors SET name = %s, description = %s, schema = %s,"
                " specimen_model_id = %s, serving_model_id = %s, updated_at = now()"
                f" WHERE id = %s RETURNING {COLUMNS}",
                (
                    edit.name,
                    edit.description,
                    Jsonb(edit.schema.document),
                    edit.roles.specimen_model_id,
                    edit.roles.serving_model_id,
                    extractor_id,
                ),
            )
            row = await cursor.fetchone()
            if row is not None and (edit.added_columns or edit.removed_columns):
                await cursor.execute(
                    REWRITE_ROWS,
                    (
                        list(edit.removed_columns),
                        Jsonb(dict.fromkeys(edit.added_columns)),
                        extractor_id,
                    ),
                )
        return None if row is None else row.as_extractor()

    async def delete(self, extractor_id: int) -> bool:
        async with self.pool.connection() as connection:
            cursor = await connection.execute(
                "DELETE FROM extractlayer.extractors WHERE id = %s",
                (extractor_id,),
            )
            return cursor.rowcount > 0
