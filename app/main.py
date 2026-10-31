import sqlite3
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from app.database import get_db
from app.routers import categories, orders, products

app = FastAPI(title="ShopStock API")
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(orders.router)


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
