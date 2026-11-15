from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class StockAdjustmentIn(BaseModel):
    change: Annotated[
        int,
        Field(
            strict=True,
            ge=-1_000_000_000,
            le=1_000_000_000,
            description="Quantity to add or remove from current stock.",
            examples=[10, -5],
        ),
    ]
    reason: Literal["restock", "damaged", "correction"] = Field(
        description="Reason for the stock adjustment.",
        examples=["restock"],
    )

    @field_validator("change")
    @classmethod
    def validate_change(cls, value: int) -> int:
        if value == 0:
            raise ValueError("stock change cannot be zero")
        return value


class StockAdjustmentOut(BaseModel):
    product_id: int = Field(description="ID of the adjusted product.", examples=[1])
    previous_quantity: int = Field(
        description="Stock quantity before adjustment.", examples=[20]
    )
    change: int = Field(description="Quantity added or removed.", examples=[10])
    new_quantity: int = Field(
        description="Stock quantity after adjustment.", examples=[30]
    )
    reason: str = Field(description="Reason for the adjustment.", examples=["restock"])
    created_at: datetime = Field(description="Date and time of the adjustment.")


class StockMovementOut(BaseModel):
    id: int = Field(
        description="Unique identifier of the stock movement.", examples=[1]
    )
    product_id: int = Field(description="ID of the related product.", examples=[1])
    change: int = Field(
        description="Quantity added or removed from stock.", examples=[10]
    )
    reason: str = Field(
        description="Reason for the stock movement.", examples=["restock"]
    )
    order_id: int | None = Field(
        description="Related order ID, if the movement was caused by an order.",
        examples=[None],
    )
    created_at: datetime = Field(description="Date and time of the stock movement.")


class PaginatedStockMovementsOut(BaseModel):
    items: list[StockMovementOut] = Field(
        description="Stock movements on the current page."
    )
    total: int = Field(description="Total matching stock movements.", examples=[50])
    page: int = Field(description="Current page number.", examples=[1])
    page_size: int = Field(description="Movements per page.", examples=[20])
    total_pages: int = Field(description="Total available pages.", examples=[3])
