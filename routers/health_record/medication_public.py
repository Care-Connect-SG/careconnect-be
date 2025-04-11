from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from db.connection import get_resident_db
from models.medication import MedicationResponse

router = APIRouter(prefix="/medications", tags=["Global Medications"])


@router.get("/{medication_id}", response_model=MedicationResponse)
async def get_medication_by_id_only(medication_id: str, db=Depends(get_resident_db)):
    if not ObjectId.is_valid(medication_id):
        raise HTTPException(status_code=400, detail="Invalid medication ID")

    record = await db["medications"].find_one({"_id": ObjectId(medication_id)})
    if not record:
        raise HTTPException(status_code=404, detail="Medication not found")

    return MedicationResponse(**record)
