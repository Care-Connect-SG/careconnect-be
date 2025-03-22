from fastapi import APIRouter, Depends, Request
from models.medication import MedicationCreate, MedicationResponse
from typing import List
from services.medication_service import (
    create_medication,
    get_medications_by_resident,
    get_medication_by_id,
    update_medication,
    delete_medication,
)
from db.connection import get_db
from utils.limiter import limiter

router = APIRouter(prefix="/residents/{resident_id}/medications", tags=["Medications"])


@router.post("/", response_model=MedicationResponse)
@limiter.limit("10/minute")
async def add_medication(
    request: Request, resident_id: str, medication: MedicationCreate, db=Depends(get_db)
):
    return await create_medication(db, resident_id, medication)


@router.get("/", response_model=List[MedicationResponse])
@limiter.limit("100/minute")
async def list_medications(request: Request, resident_id: str, db=Depends(get_db)):
    return await get_medications_by_resident(db, resident_id)


@router.get("/{medication_id}", response_model=MedicationResponse)
@limiter.limit("100/minute")
async def get_medication(
    request: Request, resident_id: str, medication_id: str, db=Depends(get_db)
):
    return await get_medication_by_id(db, resident_id, medication_id)


@router.put("/{medication_id}", response_model=MedicationResponse)
@limiter.limit("10/minute")
async def update_medication_record(
    request: Request,
    resident_id: str,
    medication_id: str,
    update_data: MedicationCreate,
    db=Depends(get_db),
):
    return await update_medication(db, resident_id, medication_id, update_data)


@router.delete("/{medication_id}")
@limiter.limit("10/minute")
async def delete_medication_record(
    request: Request, resident_id: str, medication_id: str, db=Depends(get_db)
):
    return await delete_medication(db, resident_id, medication_id)
