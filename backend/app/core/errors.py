from typing import Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Any] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class InsufficientFundsError(AppError):
    def __init__(self, message: str = "Insufficient available balance"):
        super().__init__(code="INSUFFICIENT_FUNDS", message=message, status_code=status.HTTP_400_BAD_REQUEST)


class RiskCheckFailedError(AppError):
    def __init__(self, code: str, message: str, details: Optional[Any] = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class ResourceNotFoundError(AppError):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} with identifier '{identifier}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Not enough permissions"):
        super().__init__(code="FORBIDDEN", message=message, status_code=status.HTTP_403_FORBIDDEN)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    error_payload = {
        "code": exc.code,
        "message": exc.message
    }
    if exc.details:
        error_payload["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": error_payload
        }
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            }
        }
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception during request {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later."
            }
        }
    )
