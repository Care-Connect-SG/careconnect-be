import datetime
from fastapi import HTTPException
from bson import ObjectId
from models.careplan import CarePlanCreate, CarePlanResponse


async def create_careplan(db, resident_id: str, careplan_data: CarePlanCreate):
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    careplan_dict = {
        k: v for k, v in careplan_data.dict().items() if k != "id" and v is not None
    }

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
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    resident_obj_id = ObjectId(resident_id)
    careplans = []

    cursor = db["careplans"].find({"resident_id": resident_obj_id})
    async for record in cursor:
        careplans.append(CarePlanResponse(**record))

    return careplans


async def get_careplan_by_id(db, resident_id: str, careplan_id: str):
    if not ObjectId.is_valid(careplan_id):
        raise HTTPException(status_code=400, detail="Invalid careplan ID")

    record = await db["careplans"].find_one({"_id": ObjectId(careplan_id)})
    if not record:
        raise HTTPException(status_code=404, detail="Care plan not found")

    return CarePlanResponse(**record)


async def update_careplan(
    db, resident_id: str, careplan_id: str, update_data: CarePlanCreate
):
    if not ObjectId.is_valid(careplan_id):
        raise HTTPException(status_code=400, detail="Invalid careplan ID")

    update_dict = {
        k: v
        for k, v in update_data.dict(exclude_unset=True).items()
        if k != "id" and v is not None
    }

    if "created_date" in update_dict and isinstance(
        update_dict["created_date"], datetime.date
    ):
        update_dict["created_date"] = datetime.datetime.combine(
            update_dict["created_date"], datetime.time.min
        )

    result = await db["careplans"].update_one(
        {"_id": ObjectId(careplan_id)}, {"$set": update_dict}
    )

    if result.modified_count == 0 and result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Care plan not found")

    updated_record = await db["careplans"].find_one({"_id": ObjectId(careplan_id)})
    if not updated_record:
        raise HTTPException(status_code=404, detail="Care plan not found")

    return CarePlanResponse(**updated_record)
