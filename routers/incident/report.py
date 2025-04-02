from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from db.connection import get_db
from models.report import ReportCreate, ReportResponse, ReportReviewCreate
from services.report_service import (
    add_report_review,
    approve_report,
    create_report,
    get_report_by_id,
    get_reports,
    remove_report,
    resolve_report_review,
    update_report,
)
from utils.limiter import limiter


router = APIRouter(prefix="/incident/reports", tags=["Incident Management Subsystem"])

class ResolveReportRequest(BaseModel):
    resolution: str

@router.post("/", summary="Create a new incident report", response_model=str)
@limiter.limit("10/minute")
async def create_new_report(request: Request, report: ReportCreate, db=Depends(get_db)):
    return await create_report(report, db)


@router.get(
    "/",
    summary="Retrieve incident reports",
    response_model=List[ReportResponse],
    response_model_by_alias=False,
)
@limiter.limit("100/minute")
async def list_reports(
    request: Request, status: Optional[str] = None, db=Depends(get_db)
):
    return await get_reports(status, db)


@router.get(
    "/{report_id}",
    summary="Retrieve a specific report",
    response_model=ReportResponse,
    response_model_by_alias=False,
)
@limiter.limit("100/minute")
async def get_report(request: Request, report_id: str, db=Depends(get_db)):
    return await get_report_by_id(report_id, db)


@router.put("/{report_id}", summary="Update an existing report", response_model=str)
@limiter.limit("10/minute")
async def edit_report(
    request: Request, report_id: str, report: ReportCreate, db=Depends(get_db)
):
    return await update_report(report_id, report, db)


@router.delete("/{report_id}", summary="Delete a report", response_model=None)
@limiter.limit("10/minute")
async def delete_report(request: Request, report_id: str, db=Depends(get_db)):
    return await remove_report(report_id, db)


@router.put("/{report_id}/publish", summary="Publish a report", response_model=str)
@limiter.limit("10/minute")
async def publish_report(request: Request, report_id: str, db=Depends(get_db)):
    return await approve_report(report_id, db)


@router.put("/{report_id}/review", summary="Add a report review", response_model=str)
@limiter.limit("10/minute")
async def review_report(
    request: Request, report_id: str, review_data: ReportReviewCreate, db=Depends(get_db)
):
    return await add_report_review(report_id, review_data, db)


@router.put("/{report_id}/resolve", summary="Resolve a report review", response_model=str)
@limiter.limit("10/minute")
async def resolve_report(
    request: Request, report_id: str, resolution: ResolveReportRequest, db=Depends(get_db)
):
    return await resolve_report_review(report_id, resolution.resolution, db)