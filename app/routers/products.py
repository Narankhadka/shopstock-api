import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.database import get_db
from app.schemas.product import (
    ProductCreate,
    ProductCreatedOut,
    ProductDetailOut,
    ProductOut,
    PaginatedProductsOut
)
from app.services import product_service
from app.services.product_service import DuplicateSKUError

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=PaginatedProductsOut)
def get_products(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    category_id: int | None = Query(default=None, ge=0),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    in_stock:bool    |None = None,
    search:str     | None = None,
    include_inactive: bool = False,
    sort_by: Literal["price", "name", "stock_quantity", "created_at"] = "name",
    order: Literal["asc", "desc"] = "asc",
    page: int =Query(default=1,ge=1),
    page_size: int =Query(default=10,ge=1,le=50),
   ):

    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
        ):
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
        order=order,
        page=page,
        page_size=page_size,

        )
@router.get("/{product_id}", response_model=ProductDetailOut)
def get_product(product_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]):
    product = product_service.get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=404, detail=f"Product with id {product_id} not found"
        )
    return product


@router.get("/sku/{sku}", response_model=ProductDetailOut)
def get_product_sku(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    sku: str = Path(pattern=r"^[A-Za-z]{3}-[0-9]{4}$"),
):
    # Wrong format (xyz) -> 422, because the client sent invalid input.
    # Correct format but no such product -> 404.
    product = product_service.get_product_by_sku(db, sku)
    if product is None:
        raise HTTPException(
            status_code=404, detail=f"Product with sku {sku.upper()} not found"
        )
    return product

@router.post(
    "",
    response_model=ProductCreatedOut,
    status_code=201)

def create_product(
    data: ProductCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    try:
        return product_service.create_product(db, data)

    except DuplicateSKUError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e)
            ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        ) from e