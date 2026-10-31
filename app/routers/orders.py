from fastapi import APIRouter, HTTPException, Path

from app.database import DBSession
from app.schemas.order import OrderCreate, OrderDetailOut, OrderOut
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderOut, status_code=201)
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
