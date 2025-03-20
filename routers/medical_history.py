from typing import Union, List
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.connection import get_db
from models.medical_history import (
    ConditionRecord,
    AllergyRecord,
    ChronicIllnessRecord,
    SurgicalHistoryRecord,
    ImmunizationRecord,
)
from services.medical_history_service import (
    create_condition_record,
    create_allergy_record,
    create_chronic_illness_record,
    create_surgical_history_record,
    create_immunization_record,
    update_condition_record,
    update_allergy_record,
    update_chronic_illness_record,
    update_surgical_history_record,
    update_immunization_record,
    delete_medical_record_by_id,
    get_medical_records_by_resident,
)
from utils.limiter import limiter

router = APIRouter(prefix="/medical/records", tags=["Medical History"])


@router.post(
    "/{template_type}",
    response_model=Union[
        ConditionRecord,
        AllergyRecord,
        ChronicIllnessRecord,
        SurgicalHistoryRecord,
        ImmunizationRecord,
    ],
    response_model_by_alias=False,
)
@limiter.limit("10/second")
async def create_medical_record(
    request: Request,
    template_type: str,
    record: dict,
    resident_id: str = Query(..., description="Resident ID linked to the record"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not template_type:
        raise HTTPException(
            status_code=400, detail="Template type is required in the URL"
        )

    record["resident_id"] = resident_id

    if template_type == "condition":
        return await create_condition_record(db, record)
    elif template_type == "allergy":
        return await create_allergy_record(db, record)
    elif template_type == "chronic":
        return await create_chronic_illness_record(db, record)
    elif template_type == "surgical":
        return await create_surgical_history_record(db, record)
    elif template_type == "immunization":
        return await create_immunization_record(db, record)
    else:
        raise HTTPException(status_code=400, detail="Invalid template type")


@router.put(
    "/{template_type}/{record_id}",
    response_model=Union[
        ConditionRecord,
        AllergyRecord,
        ChronicIllnessRecord,
        SurgicalHistoryRecord,
        ImmunizationRecord,
    ],
    response_model_by_alias=False,
)
@limiter.limit("10/second")
async def update_medical_record(
    request: Request,
    template_type: str,
    record_id: str,
    record: dict,
    resident_id: str = Query(..., description="Resident ID linked to the record"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not record:
        raise HTTPException(status_code=400, detail="No update data provided")

    if template_type == "condition":
        return await update_condition_record(db, record_id, resident_id, record)
    elif template_type == "allergy":
        return await update_allergy_record(db, record_id, resident_id, record)
    elif template_type == "chronic":
        return await update_chronic_illness_record(db, record_id, resident_id, record)
    elif template_type == "surgical":
        return await update_surgical_history_record(db, record_id, resident_id, record)
    elif template_type == "immunization":
        return await update_immunization_record(db, record_id, resident_id, record)
    else:
        raise HTTPException(status_code=400, detail="Invalid template type")


@router.delete("/{record_id}")
@limiter.limit("10/second")
async def delete_medical_record(
    request: Request, record_id: str, db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await delete_medical_record_by_id(db, record_id)


@router.get(
    "/resident/{resident_id}",
    response_model=List[
        Union[
            ConditionRecord,
            AllergyRecord,
            ChronicIllnessRecord,
            SurgicalHistoryRecord,
            ImmunizationRecord,
        ]
    ],
    response_model_by_alias=False,
)
@limiter.limit("10/second")
async def get_medical_records_by_resident_endpoint(
    request: Request, resident_id: str, db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await get_medical_records_by_resident(db, resident_id)
