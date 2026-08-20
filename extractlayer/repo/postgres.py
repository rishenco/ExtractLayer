from __future__ import annotations

from importlib import resources
from urllib.parse import urlsplit, urlunsplit

from psycopg import AsyncConnection
from psycopg.rows import TupleRow
from psycopg_pool import AsyncConnectionPool
from yoyo import get_backend, read_migrations

MIGRATIONS = resources.files("extractlayer") / "migrations"
YOYO_SCHEME = "postgresql+psycopg"


def yoyo_url(database_url: str) -> str:
    parts = urlsplit(database_url)
    return urlunsplit(parts._replace(scheme=YOYO_SCHEME))


def apply_migrations(database_url: str) -> None:
    backend = get_backend(yoyo_url(database_url))
    migrations = read_migrations(str(MIGRATIONS))
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


def open_pool(database_url: str) -> AsyncConnectionPool[AsyncConnection[TupleRow]]:
    return AsyncConnectionPool(database_url, open=False)
