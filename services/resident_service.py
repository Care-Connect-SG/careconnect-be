import datetime
import random
from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException

from models.resident import (
    RegistrationCreate,
    RegistrationResponse,
    ResidentTagResponse,
)


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
    registration_dict = registration_data.model_dump(exclude_unset=True)
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


async def get_residents_with_pagination(
    db, page: int = 1, limit: int = 8, search: Optional[str] = None
) -> List[RegistrationResponse]:
    if page < 1:
        page = 1
    if limit < 1:
        limit = 8

    skip = (page - 1) * limit

    query = {}

    if search and search.strip():
        query["full_name"] = {"$regex": search, "$options": "i"}

    cursor = db["resident_info"].find(query).skip(skip).limit(limit)

    residents = []
    async for record in cursor:
        residents.append(RegistrationResponse(**record))

    return residents


async def get_all_residents(db) -> List[RegistrationResponse]:
    residents = []
    cursor = db["resident_info"].find()
    async for record in cursor:
        residents.append(RegistrationResponse(**record))
    return residents


async def get_residents_count_with_search(db, search: Optional[str] = None) -> int:
    query = {}
    if search and search.strip():
        query["full_name"] = {"$regex": search, "$options": "i"}

    count = await db["resident_info"].count_documents(query)
    return count


async def get_resident_by_id(db, resident_id: str) -> RegistrationResponse:
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")
    record = await db["resident_info"].find_one({"_id": ObjectId(resident_id)})
    if not record:
        raise HTTPException(status_code=404, detail="Resident not found")
    return RegistrationResponse(**record)

async def update_resident(db, resident_id: str, update_data: RegistrationCreate) -> RegistrationResponse:
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    update_dict = update_data.model_dump(exclude_unset=True)

    # Fixing datetime.combine usage by referencing datetime.datetime and datetime.time
    if "date_of_birth" in update_dict and isinstance(update_dict["date_of_birth"], datetime.date):
        update_dict["date_of_birth"] = datetime.datetime.combine(
            update_dict["date_of_birth"], datetime.time.min
        )

    resident = await db["resident_info"].find_one({"_id": ObjectId(resident_id)})
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    # Append to additional_notes
    if "additional_notes" in update_dict:
        new_notes = update_dict.pop("additional_notes")
        if not isinstance(new_notes, list):
            raise HTTPException(status_code=400, detail="additional_notes must be a list")
        existing_notes = resident.get("additional_notes", [])
        update_dict["additional_notes"] = existing_notes + new_notes

    # Append to additional_notes_timestamp
    if "additional_notes_timestamp" in update_dict:
        raw_ts = update_dict.pop("additional_notes_timestamp")
        if not isinstance(raw_ts, list):
            raise HTTPException(status_code=400, detail="additional_notes_timestamp must be a list")
        parsed_ts = []
        for ts in raw_ts:
            if isinstance(ts, str):
                try:
                    parsed_ts.append(datetime.datetime.fromisoformat(ts))
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid timestamp format")
            elif isinstance(ts, datetime.date) and not isinstance(ts, datetime.datetime):
                parsed_ts.append(datetime.datetime.combine(ts, datetime.time.min))
            elif isinstance(ts, datetime.datetime):
                parsed_ts.append(ts)
        existing_ts = resident.get("additional_notes_timestamp", [])
        update_dict["additional_notes_timestamp"] = existing_ts + parsed_ts

    await db["resident_info"].update_one({"_id": ObjectId(resident_id)}, {"$set": update_dict})

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
    return {"detail": "Resident record deleted successfully"}


async def get_resident_tags(search_key: str, limit, db) -> List[ResidentTagResponse]:
    if search_key:
        cursor = (
            db["resident_info"]
            .find(
                {"full_name": {"$regex": search_key, "$options": "i"}},
                {"_id": 1, "full_name": 1},
            )
            .limit(limit)
        )
    else:
        cursor = db["resident_info"].find()

    residents = []
    async for record in cursor:
        resident_data = {"id": record["_id"], "name": record["full_name"]}
        residents.append(ResidentTagResponse(**resident_data))

    return residents


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
