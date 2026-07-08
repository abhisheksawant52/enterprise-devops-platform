"""Domain exceptions raised by the service layer.

These are translated into HTTP responses by exception handlers registered in ``app.main``.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base class for domain errors."""

    status_code: int = 500
    title: str = "Internal Server Error"


class NotFoundError(ServiceError):
    status_code = 404
    title = "Not Found"


class ConflictError(ServiceError):
    status_code = 409
    title = "Conflict"


class ValidationError(ServiceError):
    status_code = 422
    title = "Unprocessable Entity"
