from datetime import datetime, timedelta
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from db.connection import get_resident_db
from models.medication_log import MedicationAdministrationLog

router = APIRouter(prefix="/medication-logs", tags=["Medication Logs"])


@router.post("/", response_model=MedicationAdministrationLog)
async def log_medication_administration(
    resident_id: str, medication_id: str, db=Depends(get_resident_db)
):
    if not ObjectId.is_valid(resident_id) or not ObjectId.is_valid(medication_id):
        raise HTTPException(status_code=400, detail="Invalid resident or medication ID")

    log = {
        "resident_id": ObjectId(resident_id),
        "medication_id": ObjectId(medication_id),
        "nurse": None,  # will be filled in later
        "administered_at": datetime.utcnow(),
    }

    result = await db["medication_logs"].insert_one(log)
    log["_id"] = result.inserted_id
    return MedicationAdministrationLog(**log)


@router.get("/", response_model=List[MedicationAdministrationLog])
async def get_medication_logs(
    resident_id: Optional[str] = None,
    date: Optional[str] = Query(None, description="Format: YYYY-MM-DD"),
    db=Depends(get_resident_db),
):
    query = {}

    if resident_id:
        if not ObjectId.is_valid(resident_id):
            raise HTTPException(status_code=400, detail="Invalid resident ID")
        query["resident_id"] = ObjectId(resident_id)

    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            next_day = date_obj + timedelta(days=1)
            query["administered_at"] = {"$gte": date_obj, "$lt": next_day}
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD."
            )

    logs = []
    cursor = db["medication_logs"].find(query)
    async for log in cursor:
        logs.append(MedicationAdministrationLog(**log))

    return logs
