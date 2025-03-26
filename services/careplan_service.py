import datetime
from fastapi import HTTPException
from bson import ObjectId
from models.careplan import CarePlanCreate, CarePlanResponse


async def create_careplan(db, resident_id: str, careplan_data: CarePlanCreate):
    try:
        resident_oid = ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    careplan_dict = careplan_data.model_dump(exclude_none=True)
    careplan_dict["resident_id"] = ObjectId(resident_id)

    if "created_date" in careplan_dict and isinstance(
        careplan_dict["created_date"], datetime.date
    ):
        careplan_dict["created_date"] = datetime.datetime.combine(
            careplan_dict["created_date"], datetime.time.min
        )

    result = await db["careplans"].insert_one(careplan_dict)
    new_careplan = await db["careplans"].find_one({"_id": result.inserted_id})

    return CarePlanResponse(**new_careplan)


async def get_careplans_by_resident(db, resident_id: str):
    try:
        resident_oid = ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    resident_obj_id = ObjectId(resident_id)
    careplans = []

    cursor = db["careplans"].find({"resident_id": resident_obj_id})
    async for record in cursor:
        careplans.append(CarePlanResponse(**record))

    return careplans


async def get_careplan_by_id(db, resident_id: str, careplan_id: str):
    try:
        careplan_oid = ObjectId(careplan_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid careplan ID")

    record = await db["careplans"].find_one({"_id": careplan_oid})
    if not record:
        raise HTTPException(status_code=404, detail="Care plan not found")

    return CarePlanResponse(**record)


async def update_careplan(
    db, resident_id: str, careplan_id: str, update_data: CarePlanCreate
):
    try:
        careplan_oid = ObjectId(careplan_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid careplan ID")

    update_dict = update_data.model_dump(exclude_unset=True)

    if "created_date" in update_dict and isinstance(
        update_dict["created_date"], datetime.date
    ):
        update_dict["created_date"] = datetime.datetime.combine(
            update_dict["created_date"], datetime.time.min
        )

    result = await db["careplans"].update_one(
        {"_id": careplan_oid}, {"$set": update_dict}
    )

    if result.modified_count == 0:
        record = await db["careplans"].find_one({"_id": careplan_oid})
        if not record:
            raise HTTPException(status_code=404, detail="Care plan not found")

    updated_record = await db["careplans"].find_one({"_id": careplan_oid})
    return CarePlanResponse(**updated_record)


async def delete_careplan(db, resident_id: str, careplan_id: str):
    try:
        careplan_oid = ObjectId(careplan_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid careplan ID")

    result = await db["careplans"].delete_one({"_id": careplan_oid})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Care plan not found")

    return {"message": "Care plan deleted successfully"}
