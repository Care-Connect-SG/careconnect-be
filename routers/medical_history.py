from typing import List, Union
from fastapi import APIRouter, Depends, Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from services.medical_history_service import get_all_medical_records
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
)
from utils.limiter import limiter

router = APIRouter(prefix="/medical/records", tags=["Medical Records"])


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
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not template_type:
        raise HTTPException(
            status_code=400, detail="Template type is required in the URL"
        )

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


@router.get(
    "/all",
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
async def list_all_medical_records(
    request: Request, db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await get_all_medical_records(db)


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
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not template_type:
        raise HTTPException(
            status_code=400, detail="Template type is required in the URL"
        )

    if template_type == "condition":
        return await update_condition_record(db, record_id, record)
    elif template_type == "allergy":
        return await update_allergy_record(db, record_id, record)
    elif template_type == "chronic":
        return await update_chronic_illness_record(db, record_id, record)
    elif template_type == "surgical":
        return await update_surgical_history_record(db, record_id, record)
    elif template_type == "immunization":
        return await update_immunization_record(db, record_id, record)
    else:
        raise HTTPException(status_code=400, detail="Invalid template type")


@router.delete("/{record_id}")
@limiter.limit("10/second")
async def delete_medical_record(
    request: Request, record_id: str, db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await delete_medical_record_by_id(db, record_id)
