"""Custom application exception classes and handler registration."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application exception with status code and detail message."""

    def __init__(self, detail: str = "An error occurred", status_code: int = 500) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class NotFoundError(AppError):
    """Exception raised when a requested resource is not found (404)."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(detail=detail, status_code=404)


class ConflictError(AppError):
    """Exception raised when a resource conflict occurs (409)."""

    def __init__(self, detail: str = "Resource conflict") -> None:
        super().__init__(detail=detail, status_code=409)


class BadRequestError(AppError):
    """Exception raised for client request errors (400)."""

    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(detail=detail, status_code=400)


class AuthenticationError(AppError):
    """Exception raised when authentication fails (401)."""

    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(detail=detail, status_code=401)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        headers = {}
        if exc.status_code == 401:
            headers["WWW-Authenticate"] = "Bearer"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers if headers else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            # loc is a tuple like ('body', 'amount') — we want the last element as the field name
            field = str(error["loc"][-1]) if error["loc"] else "unknown"
            errors.append({"field": field, "message": error["msg"]})
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation failed", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
