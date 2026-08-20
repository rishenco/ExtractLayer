from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import psycopg
import pytest

from extractlayer.repo.extractors import PostgresExtractorRepo
from extractlayer.repo.postgres import apply_migrations, open_pool

DEFAULT_DATABASE_URL = "postgresql://extractlayer:extractlayer@127.0.0.1:5432/extractlayer"


def server_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def with_database(database_url: str, name: str) -> str:
    return urlunsplit(urlsplit(database_url)._replace(path=f"/{name}"))


@pytest.fixture
def empty_database() -> Iterator[str]:
    name = f"el_test_{uuid4().hex[:16]}"
    server = server_url()
    with psycopg.connect(server, autocommit=True) as connection:
        connection.execute(f'CREATE DATABASE "{name}"')
    try:
        yield with_database(server, name)
    finally:
        with psycopg.connect(server, autocommit=True) as connection:
            connection.execute(f'DROP DATABASE "{name}" WITH (FORCE)')


@pytest.fixture
async def extractors(empty_database: str) -> AsyncIterator[PostgresExtractorRepo]:
    apply_migrations(empty_database)
    pool = open_pool(empty_database)
    await pool.open()
    try:
        yield PostgresExtractorRepo(pool)
    finally:
        await pool.close()
