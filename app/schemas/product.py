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
    str,
    BeforeValidator(trim_name),
    Field(
        min_length=2,
        max_length=100,
        description="Product name. Leading and trailing whitespace is removed.",
        examples=["Wireless Mouse"],
    ),
]

ProductPrice = Annotated[
    Decimal,
    Field(
        gt=0,
        le=1000000,
        decimal_places=2,
        description="Product price in rupees.",
        examples=[1499.99],
    ),
]

ProductCategoryId = Annotated[
    int,
    Field(
        gt=0,
        le=2**31 - 1,
        strict=True,
        description="ID of the existing product category.",
        examples=[1],
    ),
]

ReorderLevel = Annotated[
    int,
    Field(
        ge=0,
        le=1000000,
        strict=True,
        description="Minimum stock quantity before reordering is needed.",
        examples=[5],
    ),
]


class ProductOut(BaseModel):
    id: int = Field(description="Unique identifier of the product.", examples=[1])
    sku: str = Field(description="Unique product SKU.", examples=["MOU-1001"])
    name: str = Field(description="Name of the product.", examples=["Wireless Mouse"])
    category_id: int = Field(description="ID of the product category.", examples=[1])
    price: float = Field(description="Product price in rupees.", examples=[1499.99])
    stock_quantity: int = Field(
        description="Current available stock quantity.", examples=[50]
    )
    is_active: bool = Field(
        description="Whether the product is active.", examples=[True]
    )
    reorder_level: int = Field(
        description="Minimum stock level for reordering.", examples=[5]
    )


class ProductDetailOut(ProductOut):
    category_name: str = Field(
        description="Name of the category this product belongs to.",
        examples=["Electronics"],
    )


class ProductCreate(BaseModel):
    sku: Annotated[
        str,
        Field(
            pattern=r"^[A-Z]{3}-[0-9]{4}$",
            description="Unique product SKU in the format ABC-1234.",
            examples=["MOU-1001"],
        ),
    ]
    name: ProductName
    category_id: ProductCategoryId
    price: ProductPrice
    stock_quantity: Annotated[
        int,
        Field(
            ge=0,
            le=1_000_000_000,
            strict=True,
            description="Initial available stock quantity.",
            examples=[50],
        ),
    ]
    reorder_level: ReorderLevel = 5


class ProductCreatedOut(ProductOut):
    created_at: datetime = Field(
        description="Date and time when the product was created.",
        examples=["2026-11-15T10:30:00"],
    )
    updated_at: datetime = Field(
        description="Date and time when the product was last updated.",
        examples=["2026-11-15T10:30:00"],
    )


class PaginatedProductsOut(BaseModel):
    items: list[ProductOut] = Field(description="Products on the current page.")
    total: int = Field(description="Total matching products.", examples=[100])
    page: int = Field(description="Current page number.", examples=[1])
    page_size: int = Field(description="Products per page.", examples=[20])
    total_pages: int = Field(description="Total available pages.", examples=[5])


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ProductName | None = None
    price: ProductPrice | None = None
    category_id: ProductCategoryId | None = None
    reorder_level: ReorderLevel | None = None
    is_active: bool | None = Field(
        default=None,
        description="Whether the product should be active.",
        examples=[True],
    )

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required")

        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")

        return self
