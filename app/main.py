import logging
import sqlite3
import time
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import get_db
from app.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.routers import categories, orders, products, reports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
request_logger = logging.getLogger("shopstock.requests")
app = FastAPI(
    title="ShopStock API",
    description=(
        "A RESTful inventory and order management API built with FastAPI. "
        "Supports product management, stock adjustments, order processing, "
        "and inventory reporting."
    ),
    version="1.0.0",
)
app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(sqlite3.IntegrityError, integrity_error_handler)  # type: ignore[arg-type]


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        request_logger.error(
            "%s %s -> 500 (%.1f ms)",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    request_logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(products.router)
app.include_router(categories.router)
app.include_router(orders.router)
app.include_router(reports.router)


@app.get(
    "/health",
    summary="Check API and database health",
    tags=["Health"],
    responses={
        200: {"description": "API and database are healthy"},
        503: {"description": "Database is unavailable"},
    },
)
def health(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    try:
        db.execute("SELECT * FROM products LIMIT 1")
    except sqlite3.Error:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )
    return {"status": "ok", "database": "connected"}
