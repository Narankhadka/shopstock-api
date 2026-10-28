import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas.category import CategoryOut
from app.services import category_service

router = APIRouter(prefix="/categories",tags=["categories"])

@router.get("",response_model=list[CategoryOut])
def get_categories(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    return category_service.list_categories(db)