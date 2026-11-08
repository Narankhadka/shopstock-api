from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.database import DBSession
from app.schemas.order import (
    OrderCreate,
    OrderDetailOut,
    OrderOut,
    OrderStatusUpdate,
    PaginatedOrdersOut,
)
from app.services import order_service
from app.security import require_api_key

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("",
             response_model=OrderOut,
             status_code=201,
             dependencies=[Depends(require_api_key)],
             )
def create_order(
    data: OrderCreate,
    db: DBSession,
):
    try:
        return order_service.create_order(db, data)
    except ValueError as e:
        message = str(e)

        if "not found" in message or "inactive" in message:
            raise HTTPException(status_code=404, detail=message) from e
        raise HTTPException(status_code=409, detail=message) from e


@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order_by_id(db: DBSession, order_id: int = Path(gt=0)):
    try:
        return order_service.get_order_by_id(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("", response_model=PaginatedOrdersOut)
def list_orders(
    db: DBSession,
    status: Literal["pending", "confirmed", "delivered", "cancelled"] | None = None,
    customer_phone: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
):
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=422, detail="date_from cannot be greater than date_to"
        )
    return order_service.list_orders(
        db=db,
        status=status,
        customer_phone=customer_phone,
        date_from=str(date_from) if date_from is not None else None,
        date_to=str(date_to) if date_to is not None else None,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{order_id}/status",
    response_model=OrderDetailOut,
    status_code=200,
    dependencies=[Depends(require_api_key)],
)
def update_order_status(
    data: OrderStatusUpdate,
    db: DBSession,
    order_id: int = Path(gt=0),
):
    try:
        return order_service.update_order_status(
            db=db,
            order_id=order_id,
            data=data,
        )

    except ValueError as exc:
        message = str(exc)

        if message == "Order not found":
            raise HTTPException(
                status_code=404,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=409,
            detail=message,
        ) from exc
