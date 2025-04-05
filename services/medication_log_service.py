from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException
from bson import ObjectId

from models.medication_log import MedicationAdministrationLog


async def create_medication_log(
    db, resident_id: str, medication_id: str
) -> MedicationAdministrationLog:
    if not ObjectId.is_valid(resident_id) or not ObjectId.is_valid(medication_id):
        raise HTTPException(status_code=400, detail="Invalid resident or medication ID")

    log = {
        "resident_id": ObjectId(resident_id),
        "medication_id": ObjectId(medication_id),
        "nurse": None,  # To be filled when auth is available
        "administered_at": datetime.utcnow(),
    }

    result = await db["medication_logs"].insert_one(log)
    log["_id"] = result.inserted_id
    return MedicationAdministrationLog(**log)


async def get_medication_logs(
    db, resident_id: Optional[str] = None, date: Optional[str] = None
) -> List[MedicationAdministrationLog]:
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
    async for record in cursor:
        logs.append(MedicationAdministrationLog(**record))

    return logs
