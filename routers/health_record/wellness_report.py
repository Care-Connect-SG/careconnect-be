from typing import List

from fastapi import APIRouter, Body, Depends, Request, status

from db.connection import get_resident_db
from models.wellness_report import WellnessReportCreate, WellnessReportResponse
from services.ai.ai_wellness_report_service import get_ai_wellness_report_suggestion
from services.user_service import get_current_user, require_roles
from services.wellness_report_service import (
    create_wellness_report,
    delete_wellness_report,
    get_reports_by_resident,
    get_wellness_report_by_id,
    update_wellness_report,
)
from utils.limiter import limiter

router = APIRouter(
    prefix="/residents/{resident_id}/wellness-reports", tags=["Wellness Reports"]
)


@router.post("/", response_model=WellnessReportResponse, response_model_by_alias=False)
@limiter.limit("10/minute")
async def add_report(
    request: Request,
    resident_id: str,
    report: WellnessReportCreate,
    db=Depends(get_resident_db),
    current_user: dict = Depends(get_current_user),
    user: dict = Depends(require_roles(["Admin", "Nurse"])),
):
    return await create_wellness_report(db, resident_id, report)


@router.get(
    "/", response_model=List[WellnessReportResponse], response_model_by_alias=False
)
@limiter.limit("10/minute")
async def get_reports(
    request: Request,
    resident_id: str,
    db=Depends(get_resident_db),
    current_user: dict = Depends(get_current_user),
    user: dict = Depends(require_roles(["Admin", "Nurse"])),
):
    return await get_reports_by_resident(db, resident_id)


@router.get(
    "/{report_id}", response_model=WellnessReportResponse, response_model_by_alias=False
)
@limiter.limit("10/minute")
async def get_report(
    request: Request,
    resident_id: str,
    report_id: str,
    db=Depends(get_resident_db),
    current_user: dict = Depends(get_current_user),
    user: dict = Depends(require_roles(["Admin", "Nurse"])),
):
    return await get_wellness_report_by_id(db, resident_id, report_id)


@router.put(
    "/{report_id}", response_model=WellnessReportResponse, response_model_by_alias=False
)
@limiter.limit("10/minute")
async def update_report(
    request: Request,
    resident_id: str,
    report_id: str,
    report: WellnessReportCreate,
    db=Depends(get_resident_db),
    current_user: dict = Depends(get_current_user),
    user: dict = Depends(require_roles(["Admin", "Nurse"])),
):
    return await update_wellness_report(db, resident_id, report_id, report)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_report(
    request: Request,
    resident_id: str,
    report_id: str,
    db=Depends(get_resident_db),
    current_user: dict = Depends(get_current_user),
    user: dict = Depends(require_roles(["Admin"])),
):
    await delete_wellness_report(db, resident_id, report_id)
    return None


@router.post(
    "/generate-suggestion",
    response_model=WellnessReportCreate,
    response_model_by_alias=False,
)
@limiter.limit("5/minute")
async def get_ai_suggestion(
    request: Request,
    resident_id: str,
    context_data: dict = Body(default={}),
    db=Depends(get_resident_db),
    current_user: dict = Depends(get_current_user),
    user: dict = Depends(require_roles(["Admin", "Nurse"])),
):
    context = context_data.get("context", "")
    ai_suggestion = await get_ai_wellness_report_suggestion(
        db, resident_id, current_user, context
    )
    return ai_suggestion
