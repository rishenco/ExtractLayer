from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from extractlayer.config import Config
from extractlayer.domain.model import ModelKind
from extractlayer.repo.model_executors.dummy import DummyModelExecutor
from extractlayer.repo.pg.datasets import PostgresDatasetRepo
from extractlayer.repo.pg.db import apply_migrations, open_pool
from extractlayer.repo.pg.extractors import PostgresExtractorRepo
from extractlayer.repo.pg.models import PostgresModelRepo
from extractlayer.repo.pg.rows import PostgresRowRepo
from extractlayer.service.datasets import DatasetService
from extractlayer.service.extractors import ExtractorService
from extractlayer.service.models import ModelService
from extractlayer.transport import http
from extractlayer.transport.datasets import dataset_routes, row_routes
from extractlayer.transport.models import model_routes


def build_app(config: Config) -> FastAPI:
    apply_migrations(config.database_url)
    pool = open_pool(config.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await pool.open()
        try:
            yield
        finally:
            await pool.close()

    extractors = PostgresExtractorRepo(pool)
    models = PostgresModelRepo(pool)
    datasets = PostgresDatasetRepo(pool)
    rows = PostgresRowRepo(pool)
    executors = {ModelKind.DUMMY: DummyModelExecutor()}
    dataset_service = DatasetService(datasets, rows, extractors)
    return http.create_app(
        [
            http.extractor_routes(ExtractorService(extractors, models, datasets, executors)),
            model_routes(ModelService(models, extractors)),
            dataset_routes(dataset_service),
            row_routes(dataset_service),
        ],
        lifespan=lifespan,
    )


def run() -> None:
    config = Config.from_environment()
    uvicorn.run(build_app(config), host=config.host, port=config.api_port)


if __name__ == "__main__":
    run()
