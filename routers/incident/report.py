from typing import Optional
from fastapi import APIRouter, Depends

from db.connection import get_db
from models.report import ReportBase
from services.report_service import create_report, get_report_by_id, get_reports, remove_report, update_report


router = APIRouter(prefix="/incident/reports", tags=["Incident Management Subsystem"])

@router.post("/")
async def create_new_report(report: ReportBase, db=Depends(get_db)):
    return await create_report(report, db)

@router.get("/")
async def list_reports(status: Optional[str] = None, db=Depends(get_db)):
    return await get_reports(status, db)

@router.get("/{report_id}")
async def get_report(report_id: str, db=Depends(get_db)):
    return await get_report_by_id(report_id, db)

@router.put("/{report_id}")
async def edit_report(report_id: str, report: ReportBase, db=Depends(get_db)):
    return await update_report(report_id, report, db)

@router.delete("/{report_id}")
async def delete_report(report_id: str, db=Depends(get_db)):
    return await remove_report(report_id, db)

