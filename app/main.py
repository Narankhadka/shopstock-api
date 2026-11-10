import sqlite3
from typing import Annotated

from fastapi import Depends, FastAPI
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



app = FastAPI(title="ShopStock API")
app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]

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
