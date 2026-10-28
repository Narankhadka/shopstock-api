from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category_id: int
    price: float
    stock_quantity: int
    is_active: bool

class ProductDetailOut(ProductOut):
    category_name:str
    