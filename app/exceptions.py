"""Custom application exception classes."""


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
