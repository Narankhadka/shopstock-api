import sqlite3

from fastapi import APIRouter, Depends,HTTPException,Query,Path
from typing import Literal
from app.database import get_db
from app.schemas.product import ProductOut,ProductDetailOut
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
@router.get("/{product_id}", response_model=ProductDetailOut)
def get_product(product_id: int, db: sqlite3.Connection = Depends(get_db)):
    product = product_service.get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=404, detail=f"Product with id {product_id} not found"
        )
    return product


@router.get("/sku/{sku}", response_model=ProductDetailOut)
def get_product_sku(
    sku: str = Path(pattern=r"^[A-Za-z]{3}-[0-9]{4}$"),
    db: sqlite3.Connection = Depends(get_db),
):
    # Wrong format (xyz) -> 422, because the client sent invalid input.
    # Correct format but no such product -> 404.
    product = product_service.get_product_by_sku(db, sku)
    if product is None:
        raise HTTPException(
            status_code=404, detail=f"Product with sku {sku.upper()} not found"
        )
    return product