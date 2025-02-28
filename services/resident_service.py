import datetime
import random
from fastapi import HTTPException
from models.resident import RegistrationCreate
from bson import ObjectId
from typing import List


async def create_residentInfo(db, registration_data: RegistrationCreate):
    # Optionally check if a registration already exists for the given NRIC
    existing = await db["resident_info"].find_one(
        {"nric_number": registration_data.nric_number}
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Registration for this NRIC already exists"
        )

    # Auto-assign a room number if not provided
    room_number = registration_data.room_number or str(random.randint(100, 999))

    # Prepare the registration object
    registration_dict = registration_data.dict()
    registration_dict["room_number"] = room_number

    # Convert date_of_birth from date to datetime (if needed)
    if isinstance(registration_dict.get("date_of_birth"), datetime.date):
        registration_dict["date_of_birth"] = datetime.datetime.combine(
            registration_dict["date_of_birth"], datetime.time.min
        )

    # Set admission_date automatically to current datetime (midnight)
    today_date = datetime.date.today()
    registration_dict["admission_date"] = datetime.datetime.combine(
        today_date, datetime.time.min
    )

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


async def get_resident_by_id(db, resident_id: str) -> dict:
    # Validate that the provided ID is a valid MongoDB ObjectId
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    # Query the database by converting the string ID to an ObjectId
    record = await db["resident_info"].find_one({"_id": ObjectId(resident_id)})
    if not record:
        raise HTTPException(status_code=404, detail="Resident not found")

    # Convert the Mongo _id to a string for the response
    record["id"] = str(record["_id"])
    del record["_id"]
    return record


async def update_resident(
    db, resident_id: str, update_data: RegistrationCreate
) -> dict:
    # Validate that the provided ID is a valid MongoDB ObjectId
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    update_dict = update_data.dict()

    # Convert date_of_birth from date to datetime (if needed)
    if "date_of_birth" in update_dict and isinstance(
        update_dict["date_of_birth"], datetime.date
    ):
        update_dict["date_of_birth"] = datetime.datetime.combine(
            update_dict["date_of_birth"], datetime.time.min
        )

    # Update the resident record using $set
    result = await db["resident_info"].update_one(
        {"_id": ObjectId(resident_id)}, {"$set": update_dict}
    )

    if result.modified_count == 0:
        # If no fields were modified, check whether the resident exists
        resident = await db["resident_info"].find_one({"_id": ObjectId(resident_id)})
        if not resident:
            raise HTTPException(status_code=404, detail="Resident not found")

    # Retrieve and return the updated record
    updated_record = await db["resident_info"].find_one({"_id": ObjectId(resident_id)})
    if not updated_record:
        raise HTTPException(status_code=404, detail="Resident not found")

    updated_record["id"] = str(updated_record["_id"])
    del updated_record["_id"]
    return updated_record


async def delete_resident(db, resident_id: str) -> dict:
    # Validate that the provided ID is a valid MongoDB ObjectId
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    # Delete the resident record
    result = await db["resident_info"].delete_one({"_id": ObjectId(resident_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resident not found")

    return {"message": "Resident record deleted successfully"}
