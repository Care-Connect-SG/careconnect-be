from fastapi import APIRouter, Depends, Request
from db.connection import get_resident_db
from models.fall_detection import (
    FallLogCreate,
    FallLogResponse,
)
from services.fall_detection_service import (
    create_fall_log,
    get_all_fall_logs,
    update_fall_log_status,
)
from utils.limiter import limiter
from typing import List

router = APIRouter(prefix="/fall-detection", tags=["Fall Detection"])


@router.post("/log", response_model=FallLogResponse)
@limiter.limit("20/minute")
async def log_fall_event(
    request: Request,
    fall_data: FallLogCreate,
    db=Depends(get_resident_db),
):
    return await create_fall_log(db, fall_data)


@router.get("/logs", response_model=List[FallLogResponse])
@limiter.limit("60/minute")
async def get_all_falls(
    request: Request,
    db=Depends(get_resident_db),
):
    return await get_all_fall_logs(db)


@router.patch("/log/{log_id}/status", response_model=FallLogResponse)
@limiter.limit("10/minute")
async def update_fall_status(
    request: Request,
    log_id: str,
    status: str,
    db=Depends(get_resident_db),
):
    return await update_fall_log_status(db, log_id, status)
