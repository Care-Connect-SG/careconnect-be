from fastapi import APIRouter, Depends, Request, HTTPException
from typing import List
from models.wellness_report import WellnessReportCreate, WellnessReportResponse
from services.wellness_report_service import (
    create_wellness_report,
    get_reports_by_resident,
    get_wellness_report_by_id,
    update_wellness_report,
    delete_wellness_report,
)
from db.connection import get_db
from utils.limiter import limiter

router = APIRouter(
    prefix="/residents/{resident_id}/wellness-reports", tags=["Wellness Reports"]
)


@router.post("/", response_model=WellnessReportResponse)
@limiter.limit("10/minute")
async def add_report(
    request: Request, resident_id: str, report: WellnessReportCreate, db=Depends(get_db)
):
    return await create_wellness_report(db, resident_id, report)


@router.get("/", response_model=List[WellnessReportResponse])
@limiter.limit("100/minute")
async def list_reports(request: Request, resident_id: str, db=Depends(get_db)):
    return await get_reports_by_resident(db, resident_id)


@router.get("/{report_id}", response_model=WellnessReportResponse)
@limiter.limit("100/minute")
async def get_report(
    request: Request, resident_id: str, report_id: str, db=Depends(get_db)
):
    return await get_wellness_report_by_id(db, resident_id, report_id)


@router.put("/{report_id}", response_model=WellnessReportResponse)
@limiter.limit("10/minute")
async def update_report(
    request: Request,
    resident_id: str,
    report_id: str,
    update_data: WellnessReportCreate,
    db=Depends(get_db),
):
    return await update_wellness_report(db, resident_id, report_id, update_data)


@router.delete("/{report_id}")
@limiter.limit("10/minute")
async def delete_report(
    request: Request, resident_id: str, report_id: str, db=Depends(get_db)
):
    return await delete_wellness_report(db, resident_id, report_id)
