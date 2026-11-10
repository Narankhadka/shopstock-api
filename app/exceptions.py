import sqlite3
import logging


from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

class AppException(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppException):
    status_code = 409
    code = "CONFLICT"


class InsufficientStockError(ConflictError):
    code = "INSUFFICIENT_STOCK"


class InvalidTransitionError(ConflictError):
    code = "INVALID_TRANSITION"

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse (
        status_code=exc.status_code,
        content={"error": {"code": exc.code,"message":exc.message}},
    )

_HTTP_ERROR_CODES={
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",

}
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": str(exc.detail)}},
        headers=exc.headers,
    )

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in err["loc"]),
            "message": err["msg"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": details,
            }
        },
    )

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Something went wrong on our side",
            }
        },
    )

async def integrity_error_handler(request: Request, exc: sqlite3.IntegrityError) -> JSONResponse:
    logger.error("IntegrityError escaped the service layer: %s", exc)
    return JSONResponse(
        status_code=409,
        content={"error": {"code": "CONFLICT", "message": "The request conflicts with existing data"}},
    )
