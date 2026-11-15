from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


def trim_name(value: object) -> object:
    if isinstance(value, str):
        value = value.strip()
        if any(ord(ch) < 32 for ch in value):
            raise ValueError("name must not contain control characters")
    return value


ProductName = Annotated[
    str, BeforeValidator(trim_name), Field(min_length=2, max_length=100)
]
ProductPrice = Annotated[Decimal, Field(gt=0, le=1000000, decimal_places=2)]
ProductCategoryId = Annotated[int, Field(gt=0, le=2**31 - 1, strict=True)]
ReorderLevel = Annotated[int, Field(ge=0, le=1000000, strict=True)]


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category_id: int
    price: float
    stock_quantity: int
    is_active: bool
    reorder_level: int


class ProductDetailOut(ProductOut):
    category_name: str


class ProductCreate(BaseModel):
    sku: Annotated[str, Field(pattern=r"^[A-Z]{3}-[0-9]{4}$")]
    name: ProductName
    category_id: ProductCategoryId
    price: ProductPrice
    stock_quantity: Annotated[int, Field(ge=0, le=1_000_000_000, strict=True)]
    reorder_level: ReorderLevel = 5


class ProductCreatedOut(ProductOut):
    created_at: datetime
    updated_at: datetime


class PaginatedProductsOut(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ProductName | None = None
    price: ProductPrice | None = None
    category_id: ProductCategoryId | None = None
    reorder_level: ReorderLevel | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required")

        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")

        return self
