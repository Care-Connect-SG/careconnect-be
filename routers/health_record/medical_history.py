from typing import List
from fastapi import APIRouter, Depends, Query, Request, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.connection import get_resident_db
from models.medical_history import (
    MedicalHistoryType,
    MedicalHistoryCreate,
    MedicalHistoryUnion,
)
from services.medical_history_service import (
    create_medical_history,
    update_medical_history,
    delete_medical_history,
    get_medical_history_by_resident,
)
from utils.limiter import limiter

router = APIRouter(
    prefix="/medical-history",
    tags=["Medical History"],
)


@router.post(
    "/",
    response_model=MedicalHistoryUnion,
    status_code=201,
    summary="Create a new medical record",
    description="Create a new medical record of the specified type for a resident",
)
@limiter.limit("10/second")
async def create_medical_history_endpoint(
    request: Request,
    record_request: MedicalHistoryCreate = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
):
    return await create_medical_history(
        db=db,
        record_type=record_request.record_type,
        resident_id=record_request.resident_id,
        record_data=record_request.record_data,
    )


@router.put(
    "/{record_id}",
    response_model=MedicalHistoryUnion,
    summary="Update a medical record",
    description="Update an existing medical record by its ID",
)
async def update_medical_history_endpoint(
    record_id: str,
    record_type: MedicalHistoryType,
    record_data: dict = Body(...),
    resident_id: str = Query(..., description="Resident ID linked to the record"),
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
):
    return await update_medical_history(
        db=db,
        record_id=record_id,
        record_type=record_type,
        resident_id=resident_id,
        update_data=record_data,
    )


@router.get(
    "/resident/{resident_id}",
    response_model=List[MedicalHistoryUnion],
    summary="Get resident's medical records",
    description="Retrieve all medical records for a specific resident",
)
@limiter.limit("10/second")
async def get_medical_history_by_resident_endpoint(
    request: Request,
    resident_id: str,
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
):
    return await get_medical_history_by_resident(db, resident_id)


@router.delete(
    "/{record_id}",
    summary="Delete a medical record",
    description="Delete a medical record by its ID",
)
async def delete_history(
    record_id: str,
    record_type: MedicalHistoryType,
    resident_id: str = Query(..., description="ID of the resident"),
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
) -> dict:
    return await delete_medical_history(
        db=db,
        record_id=record_id,
        record_type=record_type,
        resident_id=resident_id,
    )
