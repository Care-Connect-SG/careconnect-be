import datetime
import random
from fastapi import HTTPException
from models.resident import RegistrationCreate

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
    # Set admission_date automatically to current date (as an ISO string)
    registration_dict["admission_date"] = datetime.date.today().isoformat()

    # Insert into the registrations collection
    result = await db["resident_info"].insert_one(registration_dict)
    new_registration = await db["resident_info"].find_one({"_id": result.inserted_id})

    # Convert the Mongo _id to a string and assign to 'id' for the response
    new_registration["id"] = str(new_registration["_id"])
    del new_registration["_id"]
    return new_registration
