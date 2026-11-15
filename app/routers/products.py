import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.database import DBSession, get_db
from app.exceptions import NotFoundError
from app.schemas.product import (
    PaginatedProductsOut,
    ProductCreate,
    ProductCreatedOut,
    ProductDetailOut,
    ProductUpdate,
)
from app.schemas.stock import (
    PaginatedStockMovementsOut,
    StockAdjustmentIn,
    StockAdjustmentOut,
)
from app.security import require_api_key
from app.services import product_service, stock_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get(
    "",
    response_model=PaginatedProductsOut,
    summary="List products",
    responses={
        422: {
            "description": "Invalid query parameters or min_price is greater than max_price"
        },
        500: {"description": "Internal server error"},
    },
)
def get_products(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    category_id: int | None = Query(default=None, ge=0, le=2**31 - 1),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    in_stock: bool | None = None,
    search: str | None = None,
    include_inactive: bool = False,
    sort_by: Literal["price", "name", "stock_quantity", "created_at"] = "name",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(default=1, ge=1, le=1_000_000),
    page_size: int = Query(default=10, ge=1, le=50),
):

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=422, detail="min_price cannot be greater than max_price"
        )

    return product_service.list_products(
        db,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        search=search,
        include_inactive=include_inactive,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{product_id}",
    response_model=ProductDetailOut,
    summary="Get product by ID",
    responses={
        404: {"description": "Product not found"},
        422: {"description": "Invalid product ID"},
        500: {"description": "Internal server error"},
    },
)
def get_product(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    product_id: int = Path(gt=0, le=2**31 - 1),
):
    product = product_service.get_product_by_id(db, product_id)
    if product is None:
        raise NotFoundError(f"Product with id {product_id} not found")
    return product


@router.get(
    "/sku/{sku}",
    response_model=ProductDetailOut,
    summary="Get product by SKU",
    responses={
        404: {"description": "Product with the specified SKU not found"},
        422: {"description": "Invalid SKU format"},
        500: {"description": "Internal server error"},
    },
)
def get_product_sku(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    sku: str = Path(pattern=r"^[A-Za-z]{3}-[0-9]{4}$"),
):
    # Wrong format (xyz) -> 422, because the client sent invalid input.
    # Correct format but no such product -> 404.
    product = product_service.get_product_by_sku(db, sku)
    if product is None:
        raise NotFoundError(f"Product with sku {sku.upper()} not found")
    return product


@router.post(
    "",
    response_model=ProductCreatedOut,
    status_code=201,
    summary="Create a new product",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Product category not found"},
        409: {"description": "Product with this SKU already exists"},
        422: {"description": "Invalid product data"},
        500: {"description": "Internal server error"},
    },
    dependencies=[Depends(require_api_key)],
)
def create_product(
    data: ProductCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    return product_service.create_product(db, data)


@router.patch(
    "/{product_id}",
    response_model=ProductDetailOut,
    status_code=200,
    summary="Update an existing product",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Product or category not found"},
        409: {"description": "Updated SKU conflicts with an existing product"},
        422: {"description": "Invalid product ID or update data"},
        500: {"description": "Internal server error"},
    },
    dependencies=[Depends(require_api_key)],
)
def update_product(
    data: ProductUpdate,
    db: DBSession,
    product_id: int = Path(gt=0, le=2**31 - 1),
):
    return product_service.update_product(db, product_id, data)


@router.post(
    "/{product_id}/stock-adjustments",
    response_model=StockAdjustmentOut,
    status_code=201,
    summary="Adjust product stock",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Product not found"},
        409: {"description": "Stock adjustment conflicts with available stock"},
        422: {"description": "Invalid product ID or adjustment data"},
        500: {"description": "Internal server error"},
    },
    dependencies=[Depends(require_api_key)],
)
def create_stock_adjustment(
    data: StockAdjustmentIn,
    db: DBSession,
    product_id: int = Path(gt=0, le=2**31 - 1),
):
    return stock_service.adjust_stock(db, product_id, data)


@router.get(
    "/{product_id}/stock-movements",
    response_model=PaginatedStockMovementsOut,
    summary="List product stock movements",
    responses={
        404: {"description": "Product not found"},
        422: {"description": "Invalid product ID or pagination parameters"},
        500: {"description": "Internal server error"},
    },
)
def get_stock_movements(
    db: DBSession,
    product_id: int = Path(gt=0, le=2**31 - 1),
    page: int = Query(default=1, ge=1, le=1_000_000),
    page_size: int = Query(default=10, ge=1, le=50),
):
    return stock_service.list_stock_movements(db, product_id, page, page_size)


@router.delete(
    "/{product_id}",
    status_code=204,
    summary="Deactivate a product",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Product not found"},
        422: {"description": "Invalid product ID"},
        500: {"description": "Internal server error"},
    },
    dependencies=[Depends(require_api_key)],
)
def deactivate_product(
    db: DBSession,
    product_id: int = Path(gt=0, le=2**31 - 1),
) -> None:
    product_service.deactivate_product(db, product_id)


@router.post(
    "/{product_id}/restore",
    status_code=204,
    summary="Restore a deactivated product",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Product not found"},
        422: {"description": "Invalid product ID"},
        500: {"description": "Internal server error"},
    },
    dependencies=[Depends(require_api_key)],
)
def restore_product(
    db: DBSession,
    product_id: int = Path(gt=0, le=2**31 - 1),
) -> None:
    product_service.restore_product(db, product_id)
