from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from db.connection import get_resident_db
from models.medication_log import MedicationAdministrationLog
from services.medication_log_service import create_medication_log, get_medication_logs
from services.user_service import get_current_user

router = APIRouter(prefix="/medication-logs", tags=["Medication Logs"])


@router.post(
    "/", response_model=MedicationAdministrationLog, response_model_by_alias=False
)
async def log_medication_administration(
    resident_id: str,
    medication_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_resident_db),
):
    return await create_medication_log(db, resident_id, medication_id, current_user)


@router.get(
    "/", response_model=List[MedicationAdministrationLog], response_model_by_alias=False
)
async def get_medication_administration_logs(
    resident_id: Optional[str] = None,
    date: Optional[str] = Query(None, description="Format: YYYY-MM-DD"),
    db=Depends(get_resident_db),
):
    return await get_medication_logs(db, resident_id, date)
