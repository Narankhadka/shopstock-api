from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class StockAdjustmentIn(BaseModel):
    change: Annotated[int, Field(strict=True)]
    reason: Literal["restock", "damaged", "correction"]

    @field_validator("change")
    @classmethod
    def validate_change(cls, value: int) -> int:
        if value == 0:
            raise ValueError("stock change cannot be zero")
        return value


class StockAdjustmentOut(BaseModel):
    product_id: int
    previous_quantity: int
    change: int
    new_quantity: int
    reason: str
    created_at: datetime


class StockMovementOut(BaseModel):
    id: int
    product_id: int
    change: int
    reason: str
    order_id: int | None
    created_at: datetime


class PaginatedStockMovementsOut(BaseModel):
    items: list[StockMovementOut]
    total: int
    page: int
    page_size: int
    total_pages: int
