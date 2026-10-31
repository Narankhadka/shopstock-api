from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from app.schemas.product import trim_name

Customer_Name = Annotated[str, BeforeValidator(trim_name), Field(min_length=1)]


class OrderItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: Annotated[int, Field(gt=0, strict=True)]
    quantity: Annotated[int, Field(ge=1, le=100, strict=True)]


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_name: Customer_Name
    customer_phone: Annotated[str, Field(pattern=r"^(97|98)[0-9]{8}$", strict=True)]
    items: Annotated[list[OrderItemCreate], Field(min_length=1, max_length=20)]

    @model_validator(mode="after")
    def validate_unique_products(self):
        product_ids = [item.product_id for item in self.items]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Duplicate products are not allowed")

        return self


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    line_total: float


class OrderOut(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    status: str
    total_amount: float
    items: list[OrderItemOut]
    created_at: datetime
