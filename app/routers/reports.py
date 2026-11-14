from fastapi import APIRouter, Query

from app.database import DBSession
from app.schemas.report import InventorySummaryOut
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/inventory-summary", response_model=InventorySummaryOut)
def get_inventory_summary(
    db: DBSession,
    threshold: int | None = Query(default=None, ge=0),
):
    return report_service.get_inventory_summary(
        db=db,
        threshold=threshold,
    )
