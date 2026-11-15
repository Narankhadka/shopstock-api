from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from app.schemas.product import trim_name

Customer_Name = Annotated[
    str,
    BeforeValidator(trim_name),
    Field(
        min_length=1,
        description="Customer's full name. Leading and trailing whitespace is removed.",
        examples=["Ram Sharma"],
    ),
]


class OrderItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: Annotated[
        int,
        Field(
            gt=0,
            strict=True,
            description="ID of the product to order.",
            examples=[1],
        ),
    ]
    quantity: Annotated[
        int,
        Field(
            ge=1,
            le=100,
            strict=True,
            description="Number of units to order.",
            examples=[2],
        ),
    ]


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_name: Customer_Name
    customer_phone: Annotated[
        str,
        Field(
            pattern=r"^(97|98)[0-9]{8}$",
            strict=True,
            description="Customer's 10-digit Nepali mobile number.",
            examples=["9841234567"],
        ),
    ]
    items: Annotated[
        list[OrderItemCreate],
        Field(
            min_length=1,
            max_length=20,
            description="Products and quantities included in the order.",
        ),
    ]

    @model_validator(mode="after")
    def validate_unique_products(self):
        product_ids = [item.product_id for item in self.items]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Duplicate products are not allowed")

        return self


class OrderItemOut(BaseModel):
    product_id: int = Field(description="ID of the ordered product.", examples=[1])
    quantity: int = Field(description="Ordered quantity.", examples=[2])
    unit_price: float = Field(
        description="Price per unit in rupees.", examples=[500.00]
    )
    line_total: float = Field(
        description="Total price for this order item.", examples=[1000.00]
    )


class OrderOut(BaseModel):
    id: int = Field(description="Unique identifier of the order.", examples=[1])
    customer_name: str = Field(
        description="Name of the customer.", examples=["Ram Sharma"]
    )
    customer_phone: str = Field(
        description="Customer's phone number.", examples=["9841234567"]
    )
    status: str = Field(description="Current order status.", examples=["pending"])
    total_amount: float = Field(
        description="Total order amount in rupees.", examples=[1000.00]
    )
    items: list[OrderItemOut] = Field(description="Items included in the order.")
    created_at: datetime = Field(
        description="Date and time when the order was created."
    )


class OrderItemDetailOut(OrderItemOut):
    product_name: str = Field(
        description="Name of the ordered product.", examples=["Wireless Mouse"]
    )


class OrderDetailOut(BaseModel):
    id: int = Field(description="Unique identifier of the order.", examples=[1])
    customer_name: str = Field(
        description="Name of the customer.", examples=["Ram Sharma"]
    )
    customer_phone: str = Field(
        description="Customer's phone number.", examples=["9841234567"]
    )
    status: str = Field(description="Current order status.", examples=["pending"])
    total_amount: float = Field(
        description="Total order amount in rupees.", examples=[1000.00]
    )
    items: list[OrderItemDetailOut] = Field(
        description="Detailed items included in the order."
    )
    created_at: datetime = Field(
        description="Date and time when the order was created."
    )


class OrderSummaryOut(BaseModel):
    id: int = Field(description="Unique identifier of the order.", examples=[1])
    customer_name: str = Field(
        description="Name of the customer.", examples=["Ram Sharma"]
    )
    customer_phone: str = Field(
        description="Customer's phone number.", examples=["9841234567"]
    )
    status: str = Field(description="Current order status.", examples=["pending"])
    total_amount: float = Field(
        description="Total order amount in rupees.", examples=[1000.00]
    )
    item_count: int = Field(description="Number of items in the order.", examples=[2])
    created_at: datetime = Field(
        description="Date and time when the order was created."
    )


class PaginatedOrdersOut(BaseModel):
    items: list[OrderSummaryOut] = Field(description="Orders on the current page.")
    total: int = Field(description="Total matching orders.", examples=[50])
    page: int = Field(description="Current page number.", examples=[1])
    page_size: int = Field(description="Orders per page.", examples=[20])
    total_pages: int = Field(description="Total available pages.", examples=[3])


class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending", "confirmed", "delivered", "cancelled"] = Field(
        description="New status requested for the order.",
        examples=["confirmed"],
    )
