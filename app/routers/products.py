import sqlite3

from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas.product import ProductOut
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def get_products(
    category_id: int | None = None, 
    min_price: float | None = None, 
    max_price: float | None = None,
    in_stock:bool    |None = None,
    search:str     | None = None,
    include_inactive: bool = False,
    sort_by: str = "name",
    order: str = "asc",
    db = Depends(get_db)):
    return product_service.list_products(
        db, 
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock = in_stock,
        search=search,
        include_inactive=include_inactive,
        sort_by=sort_by,
        order=order
        
        )