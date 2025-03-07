import datetime
from fastapi import HTTPException
from bson import ObjectId
from models.careplan import CarePlanCreate


async def create_careplan(db, resident_id: str, careplan_data: CarePlanCreate):
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    # Convert Pydantic model to dictionary
    careplan_dict = careplan_data.dict()
    careplan_dict["resident_id"] = resident_id

    if "created_date" in careplan_dict and isinstance(
        careplan_dict["created_date"], datetime.date
    ):
        careplan_dict["created_date"] = datetime.datetime.combine(
            careplan_dict["created_date"], datetime.time.min
        )

    # Insert into MongoDB
    result = await db["careplans"].insert_one(careplan_dict)

    # Retrieve and return the newly inserted document
    new_careplan = await db["careplans"].find_one({"_id": result.inserted_id})
    new_careplan["id"] = str(new_careplan["_id"])
    del new_careplan["_id"]

    return new_careplan


async def get_careplans_by_resident(db, resident_id: str):
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    careplans = []
    cursor = db["careplans"].find({"resident_id": resident_id})
    async for record in cursor:
        record["id"] = str(record["_id"])
        del record["_id"]
        careplans.append(record)

    return careplans


async def get_careplan_by_id(db, resident_id: str, careplan_id: str):
    if not ObjectId.is_valid(careplan_id):
        raise HTTPException(status_code=400, detail="Invalid careplan ID")

    record = await db["careplans"].find_one({"_id": ObjectId(careplan_id)})
    if not record:
        raise HTTPException(status_code=404, detail="Care plan not found")

    record["id"] = str(record["_id"])
    del record["_id"]

    return record


async def update_careplan(
    db, resident_id: str, careplan_id: str, update_data: CarePlanCreate
):
    if not ObjectId.is_valid(careplan_id):
        raise HTTPException(status_code=400, detail="Invalid careplan ID")

    update_dict = update_data.dict(exclude_unset=True)
    if "created_date" in update_dict and isinstance(
        update_dict["created_date"], datetime.date
    ):
        update_dict["created_date"] = datetime.datetime.combine(
            update_dict["created_date"], datetime.time.min
        )

    result = await db["careplans"].update_one(
        {"_id": ObjectId(careplan_id)}, {"$set": update_dict}
    )

    if result.modified_count == 0:
        record = await db["careplans"].find_one({"_id": ObjectId(careplan_id)})
        if not record:
            raise HTTPException(status_code=404, detail="Care plan not found")

    updated_record = await db["careplans"].find_one({"_id": ObjectId(careplan_id)})
    updated_record["id"] = str(updated_record["_id"])
    del updated_record["_id"]

    return updated_record
