from typing import Union, List
from fastapi import APIRouter, Depends, Request, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.connection import get_resident_db
from models.medical_history import (
    ConditionRecord,
    AllergyRecord,
    ChronicIllnessRecord,
    SurgicalHistoryRecord,
    ImmunizationRecord,
)
from services.medical_history_service import (
    create_medical_history_by_template,
    update_medical_record_by_type,
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
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
):
    return await create_medical_history_by_template(
        db, template_type, resident_id, record
    )


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
    db: AsyncIOMotorDatabase = Depends(get_resident_db),
):
    return await update_medical_record_by_type(
        db, template_type, resident_id, record_id, record
    )


@router.delete("/{record_id}")
@limiter.limit("10/second")
async def delete_medical_record(
    request: Request, record_id: str, db: AsyncIOMotorDatabase = Depends(get_resident_db)
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
    request: Request, resident_id: str, db: AsyncIOMotorDatabase = Depends(get_resident_db)
):
    return await get_medical_records_by_resident(db, resident_id)
