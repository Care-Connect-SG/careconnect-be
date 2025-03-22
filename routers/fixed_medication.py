from fastapi import APIRouter, HTTPException
from services.fixed_medication import get_all_medications, get_medication_by_id

router = APIRouter(prefix="/fixedmedications", tags=["Fixed Medications"])


@router.get("/", response_model=list)
async def list_medications():
    """Retrieve all stored medications (fixed database)"""
    return get_all_medications()


@router.get("/{medication_id}", response_model=dict)
async def get_medication(medication_id: str):
    """Retrieve medication details by scanning the barcode"""
    medication = get_medication_by_id(medication_id)
    if medication:
        return medication
    raise HTTPException(status_code=404, detail="Medication not found")
