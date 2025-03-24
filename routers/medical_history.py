from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from db.connection import get_db
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
async def create_record(
    request: CreateMedicalRecordRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> BaseMedicalRecord:
    """
    Create a new medical record with the following data:
    - **record_type**: Type of medical record (condition, allergy, chronic, surgical, immunization)
    - **resident_id**: ID of the resident this record belongs to
    - **record_data**: Data specific to the record type
    """
    return await create_medical_record(
        db=db,
        record_type=request.record_type,
        resident_id=request.resident_id,
        record_data=request.record_data,
    )

@router.put(
    "/{record_id}",
    response_model=MedicalRecordUnion,
    summary="Update a medical record",
    description="Update an existing medical record by its ID",
)
async def update_record(
    record_id: str,
    record_type: MedicalRecordType,
    resident_id: str = Query(..., description="ID of the resident"),
    update_data: dict = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> BaseMedicalRecord:
    """
    Update a medical record with the following parameters:
    - **record_id**: ID of the record to update
    - **record_type**: Type of medical record
    - **resident_id**: ID of the resident this record belongs to
    - **update_data**: New data for the record
    """
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    return await update_medical_record(
        db=db,
        record_id=record_id,
        record_type=record_type,
        resident_id=resident_id,
        update_data=update_data,
    )

@router.get(
    "/resident/{resident_id}",
    response_model=List[MedicalRecordUnion],
    summary="Get resident's medical records",
    description="Retrieve all medical records for a specific resident",
)
async def get_resident_records(
    resident_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[BaseMedicalRecord]:
    """
    Get all medical records for a resident:
    - **resident_id**: ID of the resident
    Returns a list of medical records with full details for each record type
    """
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
    db: AsyncIOMotorDatabase = Depends(get_db),
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
