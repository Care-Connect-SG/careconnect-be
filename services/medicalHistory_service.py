import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from typing import List, Union
from models.medicalHistory import (
    ConditionRecord,
    AllergyRecord,
    ChronicIllnessRecord,
    SurgicalHistoryRecord,
    ImmunizationRecord,
)


async def create_condition_record(
    db: AsyncIOMotorDatabase, data: dict
) -> ConditionRecord:
    try:
        record = ConditionRecord.parse_obj(data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error parsing condition record: {e}"
        )

    insert_data = record.dict()
    # Convert all Python date fields to datetime
    for field, value in insert_data.items():
        if isinstance(value, datetime.date) and not isinstance(
            value, datetime.datetime
        ):
            insert_data[field] = datetime.datetime.combine(value, datetime.time.min)

    result = await db["conditions"].insert_one(insert_data)
    new_record = await db["conditions"].find_one({"_id": result.inserted_id})
    if not new_record:
        raise HTTPException(status_code=500, detail="Failed to create condition record")
    new_record["_id"] = str(new_record["_id"])
    return ConditionRecord.parse_obj(new_record)


async def create_allergy_record(db: AsyncIOMotorDatabase, data: dict) -> AllergyRecord:
    try:
        record = AllergyRecord.parse_obj(data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error parsing allergy record: {e}"
        )

    insert_data = record.dict()
    for field, value in insert_data.items():
        if isinstance(value, datetime.date) and not isinstance(
            value, datetime.datetime
        ):
            insert_data[field] = datetime.datetime.combine(value, datetime.time.min)

    result = await db["allergies"].insert_one(insert_data)
    new_record = await db["allergies"].find_one({"_id": result.inserted_id})
    if not new_record:
        raise HTTPException(status_code=500, detail="Failed to create allergy record")
    new_record["_id"] = str(new_record["_id"])
    return AllergyRecord.parse_obj(new_record)


async def create_chronic_illness_record(
    db: AsyncIOMotorDatabase, data: dict
) -> ChronicIllnessRecord:
    try:
        record = ChronicIllnessRecord.parse_obj(data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error parsing chronic illness record: {e}"
        )

    insert_data = record.dict()
    for field, value in insert_data.items():
        if isinstance(value, datetime.date) and not isinstance(
            value, datetime.datetime
        ):
            insert_data[field] = datetime.datetime.combine(value, datetime.time.min)

    result = await db["chronic_illnesses"].insert_one(insert_data)
    new_record = await db["chronic_illnesses"].find_one({"_id": result.inserted_id})
    if not new_record:
        raise HTTPException(
            status_code=500, detail="Failed to create chronic illness record"
        )
    new_record["_id"] = str(new_record["_id"])
    return ChronicIllnessRecord.parse_obj(new_record)


async def create_surgical_history_record(
    db: AsyncIOMotorDatabase, data: dict
) -> SurgicalHistoryRecord:
    try:
        record = SurgicalHistoryRecord.parse_obj(data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error parsing surgical history record: {e}"
        )

    insert_data = record.dict()
    for field, value in insert_data.items():
        if isinstance(value, datetime.date) and not isinstance(
            value, datetime.datetime
        ):
            insert_data[field] = datetime.datetime.combine(value, datetime.time.min)

    result = await db["surgical_history"].insert_one(insert_data)
    new_record = await db["surgical_history"].find_one({"_id": result.inserted_id})
    if not new_record:
        raise HTTPException(
            status_code=500, detail="Failed to create surgical history record"
        )
    new_record["_id"] = str(new_record["_id"])
    return SurgicalHistoryRecord.parse_obj(new_record)


async def create_immunization_record(
    db: AsyncIOMotorDatabase, data: dict
) -> ImmunizationRecord:
    try:
        record = ImmunizationRecord.parse_obj(data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error parsing immunization record: {e}"
        )

    insert_data = record.dict()
    for field, value in insert_data.items():
        if isinstance(value, datetime.date) and not isinstance(
            value, datetime.datetime
        ):
            insert_data[field] = datetime.datetime.combine(value, datetime.time.min)

    result = await db["immunizations"].insert_one(insert_data)
    new_record = await db["immunizations"].find_one({"_id": result.inserted_id})
    if not new_record:
        raise HTTPException(
            status_code=500, detail="Failed to create immunization record"
        )
    new_record["_id"] = str(new_record["_id"])
    return ImmunizationRecord.parse_obj(new_record)


async def get_all_medical_records(db: AsyncIOMotorDatabase) -> List[
    Union[
        ConditionRecord,
        AllergyRecord,
        ChronicIllnessRecord,
        SurgicalHistoryRecord,
        ImmunizationRecord,
    ]
]:
    try:
        conditions = []
        async for record in db["conditions"].find():
            record["_id"] = str(record["_id"])
            conditions.append(ConditionRecord.parse_obj(record))

        allergies = []
        async for record in db["allergies"].find():
            record["_id"] = str(record["_id"])
            allergies.append(AllergyRecord.parse_obj(record))

        chronic = []
        async for record in db["chronic_illnesses"].find():
            record["_id"] = str(record["_id"])
            chronic.append(ChronicIllnessRecord.parse_obj(record))

        surgical = []
        async for record in db["surgical_history"].find():
            record["_id"] = str(record["_id"])
            surgical.append(SurgicalHistoryRecord.parse_obj(record))

        immunizations = []
        async for record in db["immunizations"].find():
            record["_id"] = str(record["_id"])
            immunizations.append(ImmunizationRecord.parse_obj(record))

        return conditions + allergies + chronic + surgical + immunizations
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching medical records: {e}"
        )
