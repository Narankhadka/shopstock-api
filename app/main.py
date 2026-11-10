import sqlite3
import logging
import time
from typing import Annotated

from fastapi import Depends, FastAPI,Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import get_db
from app.routers import categories, orders, products, reports
from fastapi.exceptions import RequestValidationError
from app.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
request_logger = logging.getLogger("shopstock.requests")
app = FastAPI(title="ShopStock API")
app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
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


@app.get("/health")
def health(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    try:
        db.execute("SELECT * FROM products LIMIT 1")
    except sqlite3.Error:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )
    return {"status": "ok", "database": "connected"}
