from decimal import Decimal

from pydantic import BaseModel


class LowStockItemOut(BaseModel):
    id: int
    sku: str
    name: str
    category_name: str
    stock_quantity: int


class CategoryInventoryOut(BaseModel):
    category_id: int
    category_name: str
    total_products: int
    total_stock_units: int
    total_stock_value: Decimal
    out_of_stock_count: int


class InventorySummaryOut(BaseModel):
    total_products: int
    total_stock_units: int
    total_stock_value: Decimal
    out_of_stock_count: int
    low_stock: list[LowStockItemOut]
    categories: list[CategoryInventoryOut]
