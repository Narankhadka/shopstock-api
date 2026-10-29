from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    name: str
    active_product_count: int
