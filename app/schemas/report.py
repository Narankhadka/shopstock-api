from decimal import Decimal

from pydantic import BaseModel, Field


class LowStockItemOut(BaseModel):
    id: int = Field(description="Unique identifier of the product.", examples=[1])
    sku: str = Field(description="Product's stock keeping unit.", examples=["MOU-001"])
    name: str = Field(description="Name of the product.", examples=["Wireless Mouse"])
    category_name: str = Field(
        description="Name of the product's category.",
        examples=["Electronics"],
    )
    stock_quantity: int = Field(
        description="Current available stock quantity.",
        examples=[3],
    )


class CategoryInventoryOut(BaseModel):
    category_id: int = Field(
        description="Unique identifier of the category.",
        examples=[1],
    )
    category_name: str = Field(
        description="Name of the category.",
        examples=["Electronics"],
    )
    total_products: int = Field(
        description="Total number of products in the category.",
        examples=[25],
    )
    total_stock_units: int = Field(
        description="Combined stock quantity of products in the category.",
        examples=[150],
    )
    total_stock_value: Decimal = Field(
        description="Total inventory value of the category in rupees.",
        examples=[75000.00],
    )
    out_of_stock_count: int = Field(
        description="Number of products with zero stock.",
        examples=[2],
    )


class InventorySummaryOut(BaseModel):
    total_products: int = Field(
        description="Total number of products in inventory.",
        examples=[100],
    )
    total_stock_units: int = Field(
        description="Combined stock quantity across all products.",
        examples=[500],
    )
    total_stock_value: Decimal = Field(
        description="Total inventory value in rupees.",
        examples=[250000.00],
    )
    out_of_stock_count: int = Field(
        description="Number of products currently out of stock.",
        examples=[5],
    )
    low_stock: list[LowStockItemOut] = Field(
        description="Products whose stock is at or below the low-stock threshold."
    )
    categories: list[CategoryInventoryOut] = Field(
        description="Inventory summary grouped by category."
    )
