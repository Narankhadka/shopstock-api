from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field


def trim_name(value:object) -> object:
    if isinstance(value,str):
        return value.strip()
    return value

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
    
class ProductCreate(BaseModel):
    sku:Annotated[str, Field(pattern=r"^[A-Z]{3}-[0-9]{4}$")]
    name:Annotated[
        str,
        BeforeValidator(trim_name),
        Field(min_length=2,max_length=100)]
    category_id: Annotated[int , Field(gt=0, strict=True)]
    price: Annotated[
        Decimal,
        Field(gt=0,le=1000000,decimal_places=2) ]
    stock_quantity: Annotated[int , Field(ge=0, strict=True)]
    
class ProductCreatedOut(ProductOut):
    created_at: datetime
    updated_at:datetime

class PaginatedProductsOut(BaseModel):
    items:list[ProductOut]
    total: int
    page: int 
    page_size: int 
    total_pages: int 
    