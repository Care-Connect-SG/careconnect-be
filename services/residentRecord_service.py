import datetime
import random
from fastapi import HTTPException
from models.resident import RegistrationCreate
from typing import List

async def create_residentInfo(db, registration_data: RegistrationCreate):
    # Optionally check if a registration already exists for the given NRIC
    existing = await db["resident_info"].find_one({"nric_number": registration_data.nric_number})
    if existing:
        raise HTTPException(status_code=400, detail="Registration for this NRIC already exists")

    # Auto-assign a room number if not provided
    room_number = registration_data.room_number or str(random.randint(100, 999))

    # Prepare the registration object
    registration_dict = registration_data.dict()
    registration_dict["room_number"] = room_number

    # Convert date_of_birth from date to datetime (if needed)
    if isinstance(registration_dict.get("date_of_birth"), datetime.date):
        registration_dict["date_of_birth"] = datetime.datetime.combine(registration_dict["date_of_birth"], datetime.time.min)

    # Set admission_date automatically to current datetime (midnight)
    today_date = datetime.date.today()
    registration_dict["admission_date"] = datetime.datetime.combine(today_date, datetime.time.min)

    # Insert into the resident_info collection
    result = await db["resident_info"].insert_one(registration_dict)
    new_registration = await db["resident_info"].find_one({"_id": result.inserted_id})

    # Convert the Mongo _id to a string and assign to 'id' for the response
    new_registration["id"] = str(new_registration["_id"])
    del new_registration["_id"]
    return new_registration


async def get_all_residents(db) -> List[dict]:
    residents = []
    cursor = db["resident_info"].find()
    async for record in cursor:
        # Convert Mongo _id to string and assign it to 'id'
        record["id"] = str(record["_id"])
        del record["_id"]
        # (Optional) If your dates are stored as datetime, they will be serialized properly.
        residents.append(record)
    return residents

from fastapi import HTTPException

async def get_residents_by_name(db, name: str) -> List[dict]:
    residents = []
    # Using a regex to search for the substring in the full_name field, case-insensitive
    cursor = db["resident_info"].find({"full_name": {"$regex": name, "$options": "i"}})
    async for record in cursor:
        # Convert Mongo _id to string for the response
        record["id"] = str(record["_id"])
        del record["_id"]
        residents.append(record)
    return residents

