import sqlite3

from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas.product import ProductOut
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def get_products(db: sqlite3.Connection = Depends(get_db)):
    return product_service.list_products(db)