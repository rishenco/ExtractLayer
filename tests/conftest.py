from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import psycopg
import pytest

from extractlayer.domain.model import ModelKind
from extractlayer.repo.model_executors.dummy import DummyModelExecutor
from extractlayer.repo.pg.datasets import PostgresDatasetRepo
from extractlayer.repo.pg.db import Pool, apply_migrations, open_pool
from extractlayer.repo.pg.extractors import PostgresExtractorRepo
from extractlayer.repo.pg.models import PostgresModelRepo
from extractlayer.repo.pg.rows import PostgresRowRepo
from extractlayer.service.datasets import DatasetService
from extractlayer.service.extractors import ExtractorService
from extractlayer.service.models import ModelService

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
async def pool(empty_database: str) -> AsyncIterator[Pool]:
    apply_migrations(empty_database)
    opened = open_pool(empty_database)
    await opened.open()
    try:
        yield opened
    finally:
        await opened.close()


@pytest.fixture
def extractors(pool: Pool) -> PostgresExtractorRepo:
    return PostgresExtractorRepo(pool)


@pytest.fixture
def models(pool: Pool) -> PostgresModelRepo:
    return PostgresModelRepo(pool)


@pytest.fixture
def datasets(pool: Pool) -> PostgresDatasetRepo:
    return PostgresDatasetRepo(pool)


@pytest.fixture
def rows(pool: Pool) -> PostgresRowRepo:
    return PostgresRowRepo(pool)


@pytest.fixture
def extractor_service(
    extractors: PostgresExtractorRepo,
    models: PostgresModelRepo,
    datasets: PostgresDatasetRepo,
) -> ExtractorService:
    return ExtractorService(
        extractors, models, datasets, {ModelKind.DUMMY: DummyModelExecutor()}
    )


@pytest.fixture
def model_service(
    models: PostgresModelRepo, extractors: PostgresExtractorRepo
) -> ModelService:
    return ModelService(models, extractors)


@pytest.fixture
def dataset_service(
    datasets: PostgresDatasetRepo,
    rows: PostgresRowRepo,
    extractors: PostgresExtractorRepo,
) -> DatasetService:
    return DatasetService(datasets, rows, extractors)
