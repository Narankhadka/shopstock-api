from pydantic import BaseModel, Field


class CategoryOut(BaseModel):
    id: int = Field(description="Unique identifier of the category.", examples=[1])
    name: str = Field(description="Name of the category.", examples=["Electronics"])
    active_product_count: int = Field(
        description="Number of active products in this category.",
        examples=[15],
    )
