import datetime
import random
from fastapi import HTTPException
from bson import ObjectId
from typing import List

from models.resident import RegistrationCreate, RegistrationResponse


async def create_residentInfo(
    db, registration_data: RegistrationCreate
) -> RegistrationResponse:
    existing = await db["resident_info"].find_one(
        {"nric_number": registration_data.nric_number}
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Registration for this NRIC already exists"
        )
    room_number = registration_data.room_number or str(random.randint(100, 999))
    registration_dict = registration_data.dict()
    registration_dict.pop("_id", None)
    if isinstance(registration_dict.get("date_of_birth"), datetime.date):
        registration_dict["date_of_birth"] = datetime.datetime.combine(
            registration_dict["date_of_birth"], datetime.time.min
        )
    if isinstance(registration_dict.get("additional_notes_timestamp"), datetime.date):
        registration_dict["additional_notes_timestamp"] = datetime.datetime.combine(
            registration_dict["additional_notes_timestamp"], datetime.time.min
        )
    today_date = datetime.date.today()
    registration_dict["admission_date"] = datetime.datetime.combine(
        today_date, datetime.time.min
    )
    registration_dict["room_number"] = room_number

    result = await db["resident_info"].insert_one(registration_dict)
    new_record = await db["resident_info"].find_one({"_id": result.inserted_id})
    return RegistrationResponse(**new_record)


async def get_all_residents(db) -> List[RegistrationResponse]:
    residents = []
    cursor = db["resident_info"].find()
    async for record in cursor:
        residents.append(RegistrationResponse(**record))
    return residents


async def get_residents_by_name(db, name: str) -> List[RegistrationResponse]:
    residents = []
    cursor = db["resident_info"].find({"full_name": {"$regex": name, "$options": "i"}})
    async for record in cursor:
        residents.append(RegistrationResponse(**record))
    return residents


async def get_resident_by_id(db, resident_id: str) -> RegistrationResponse:
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")
    record = await db["resident_info"].find_one({"_id": ObjectId(resident_id)})
    if not record:
        raise HTTPException(status_code=404, detail="Resident not found")
    return RegistrationResponse(**record)


async def update_resident(
    db, resident_id: str, update_data: RegistrationCreate
) -> RegistrationResponse:
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")
    update_dict = update_data.dict()
    if "date_of_birth" in update_dict and isinstance(
        update_dict["date_of_birth"], datetime.date
    ):
        update_dict["date_of_birth"] = datetime.datetime.combine(
            update_dict["date_of_birth"], datetime.time.min
        )
    if "additional_notes_timestamp" in update_dict and isinstance(
        update_dict.get("additional_notes_timestamp"), datetime.date
    ):
        update_dict["additional_notes_timestamp"] = datetime.datetime.combine(
            update_dict["additional_notes_timestamp"], datetime.time.min
        )
    result = await db["resident_info"].update_one(
        {"_id": ObjectId(resident_id)}, {"$set": update_dict}
    )
    if result.modified_count == 0:
        resident = await db["resident_info"].find_one({"_id": ObjectId(resident_id)})
        if not resident:
            raise HTTPException(status_code=404, detail="Resident not found")
    updated_record = await db["resident_info"].find_one({"_id": ObjectId(resident_id)})
    if not updated_record:
        raise HTTPException(status_code=404, detail="Resident not found")
    return RegistrationResponse(**updated_record)


async def delete_resident(db, resident_id: str) -> dict:
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")
    result = await db["resident_info"].delete_one({"_id": ObjectId(resident_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resident not found")
    return {"message": "Resident record deleted successfully"}


async def get_resident_full_name(db, resident_id: str) -> str:
    user = await db.resident_info.find_one(
        {"_id": ObjectId(resident_id)}, {"full_name": 1}
    )
    return user["full_name"] if user and "full_name" in user else "Unknown"


async def get_resident_room(db, resident_id: str) -> str:
    resident = await db.resident_info.find_one(
        {"_id": ObjectId(resident_id)}, {"room_number": 1}
    )
    return (
        resident["room_number"] if resident and "room_number" in resident else "Unknown"
    )
