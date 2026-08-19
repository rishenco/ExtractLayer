from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_HOST = "0.0.0.0"
DEFAULT_API_PORT = 8420


@dataclass(frozen=True)
class Config:
    database_url: str
    host: str
    api_port: int

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> Config:
        source = os.environ if environment is None else environment
        database_url = source.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is unset, so there is no store to serve from")
        return cls(
            database_url=database_url,
            host=source.get("HOST", DEFAULT_HOST),
            api_port=int(source.get("API_PORT", DEFAULT_API_PORT)),
        )
