from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from db.connection import get_resident_db
from models.medical_history import (
    MedicalRecordType,
    BaseMedicalRecord,
    ConditionRecord,
    AllergyRecord,
    ChronicIllnessRecord,
    SurgicalHistoryRecord,
    ImmunizationRecord,
    CreateMedicalRecordRequest,
)
from services.medical_history_service import (
    create_medical_record,
    update_medical_record,
    delete_medical_record,
    get_medical_records_by_resident,
    create_medical_history_by_template,
    update_medical_record_by_type,
    delete_medical_record_by_id,
)
from utils.limiter import limiter

router = APIRouter(
    prefix="/medical-records",
    tags=["Medical Records"],
    responses={404: {"description": "Record not found"}},
)

# Define a type that can be any of the medical record types
MedicalRecordUnion = Union[
    ConditionRecord,
    AllergyRecord,
    ChronicIllnessRecord,
    SurgicalHistoryRecord,
    ImmunizationRecord
]

@router.post(
    "/",
    response_model=MedicalRecordUnion,
    status_code=201,
    summary="Create a new medical record",
    description="Create a new medical record of the specified type for a resident",
)
@limiter.limit("10/second")
async def create_medical_record(
    request: Request,
    template_type: str,
    record: dict,
    resident_id: str = Query(..., description="Resident ID linked to the record"),
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
):
    return await create_medical_history_by_template(
        db, template_type, resident_id, record
    )

@router.put(
    "/{record_id}",
    response_model=MedicalRecordUnion,
    summary="Update a medical record",
    description="Update an existing medical record by its ID",
)
async def update_record(
    record_id: str,
    record: dict,
    resident_id: str = Query(..., description="Resident ID linked to the record"),
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
):
    return await update_medical_record_by_type(
        db, template_type, resident_id, record_id, record
    )

@router.delete("/{record_id}")
@limiter.limit("10/second")
async def delete_medical_record(
    request: Request,
    record_id: str,
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
):
    return await delete_medical_record_by_id(db, record_id)

@router.get(
    "/resident/{resident_id}",
    response_model=List[MedicalRecordUnion],
    summary="Get resident's medical records",
    description="Retrieve all medical records for a specific resident",
)
@limiter.limit("10/second")
async def get_medical_records_by_resident_endpoint(
    request: Request,
    resident_id: str,
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
):
    return await get_medical_records_by_resident(db, resident_id)

@router.delete(
    "/{record_id}",
    summary="Delete a medical record",
    description="Delete a medical record by its ID",
)
async def delete_record(
    record_id: str,
    record_type: MedicalRecordType,
    resident_id: str = Query(..., description="ID of the resident"),
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
) -> dict:
    """
    Delete a medical record with the following parameters:
    - **record_id**: ID of the record to delete
    - **record_type**: Type of medical record
    - **resident_id**: ID of the resident this record belongs to
    """
    return await delete_medical_record(
        db=db,
        record_id=record_id,
        record_type=record_type,
        resident_id=resident_id,
    )
