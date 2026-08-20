from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from extractlayer.config import Config
from extractlayer.repo.extractors import PostgresExtractorRepo
from extractlayer.repo.postgres import apply_migrations, open_pool
from extractlayer.service.extractors import ExtractorService
from extractlayer.transport import http


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

    repo = PostgresExtractorRepo(pool)
    service = ExtractorService(repo)
    return http.create_app(service, lifespan=lifespan)


def run() -> None:
    config = Config.from_environment()
    uvicorn.run(build_app(config), host=config.host, port=config.api_port)


if __name__ == "__main__":
    run()
