from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

from extractlayer.domain.errors import DomainError, NotFoundError, ValidationError

NOT_FOUND = 404
UNPROCESSABLE = 422
OTHER_DOMAIN_ERROR = 400

STATUS_BY_ERROR: tuple[tuple[type[DomainError], int], ...] = (
    (NotFoundError, NOT_FOUND),
    (ValidationError, UNPROCESSABLE),
)


def status_for(error: DomainError) -> int:
    for error_type, status in STATUS_BY_ERROR:
        if isinstance(error, error_type):
            return status
    return OTHER_DOMAIN_ERROR


async def domain_error_response(_request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, DomainError)
    details = error.details if isinstance(error, ValidationError) else {}
    return JSONResponse(
        status_code=status_for(error),
        content={"error": str(error), "details": details},
    )


async def request_error_response(_request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    details: dict[str, str] = {}
    for entry in error.errors():
        path = ".".join(str(part) for part in entry["loc"] if part not in ("body", "query"))
        details[path or "body"] = entry["msg"]
    return JSONResponse(
        status_code=UNPROCESSABLE,
        content={"error": "the request does not match the API", "details": details},
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_response)
    app.add_exception_handler(RequestValidationError, request_error_response)
