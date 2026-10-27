import sqlite3

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from app.database import get_db

app = FastAPI(title="ShopStock API")

@app.get('/health')
def health(db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute("SELECT * FROM products LIMIT 1")
    except sqlite3.Error:
        return JSONResponse(
            status_code=503,
            content={'status':'error','database':'unavailable'},
        )
    return {'status':'ok','database':'connected'}