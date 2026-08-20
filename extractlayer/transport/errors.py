from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_502_BAD_GATEWAY,
)

from extractlayer.domain.errors import (
    DomainError,
    NotFoundError,
    UpstreamModelError,
    ValidationError,
)

STATUS_BY_ERROR: tuple[tuple[type[DomainError], int], ...] = (
    (NotFoundError, HTTP_404_NOT_FOUND),
    (ValidationError, HTTP_422_UNPROCESSABLE_CONTENT),
    (UpstreamModelError, HTTP_502_BAD_GATEWAY),
)


def status_for(error: DomainError) -> int:
    for error_type, status in STATUS_BY_ERROR:
        if isinstance(error, error_type):
            return status
    return HTTP_400_BAD_REQUEST


async def domain_error_response(_request: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, DomainError):
        raise error
    details = error.details if isinstance(error, ValidationError) else {}
    return JSONResponse(
        status_code=status_for(error),
        content={"error": str(error), "details": details},
    )


async def request_error_response(_request: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, RequestValidationError):
        raise error
    details: dict[str, str] = {}
    for entry in error.errors():
        path = ".".join(str(part) for part in entry["loc"] if part not in ("body", "query"))
        details[path or "body"] = entry["msg"]
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_CONTENT,
        content={"error": "the request does not match the API", "details": details},
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_response)
    app.add_exception_handler(RequestValidationError, request_error_response)
