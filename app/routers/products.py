import sqlite3

from fastapi import APIRouter, Depends,HTTPException,Query
from typing import Literal
from app.database import get_db
from app.schemas.product import ProductOut
from app.services import product_service


router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def get_products(
    category_id: int | None = Query(default=None, ge=0),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    in_stock:bool    |None = None,
    search:str     | None = None,
    include_inactive: bool = False,
    sort_by: Literal["price", "name", "stock_quantity", "created_at"] = "name",
    order: Literal["asc", "desc"] = "asc",
    db = Depends(get_db)):
    
    if min_price is not None and max_price is not None:
        if min_price > max_price:
            raise HTTPException(
             status_code=422,
             detail="min_price cannot be greater than max_price" )

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