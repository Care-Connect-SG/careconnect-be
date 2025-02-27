import datetime
from fastapi import HTTPException
from bson import ObjectId
from models.medication import MedicationCreate

async def create_medication(db, resident_id: str, medication_data: MedicationCreate):
    
    # Validate resident_id format
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")
    
    # Convert medication data to dictionary and add resident_id
    medication_dict = medication_data.dict()
    medication_dict["resident_id"] = resident_id  # Link medication to resident
    
    # Convert date fields to datetime if needed
    if "start_date" in medication_dict and isinstance(medication_dict["start_date"], datetime.date):
        medication_dict["start_date"] = datetime.datetime.combine(medication_dict["start_date"], datetime.time.min)

    if "end_date" in medication_dict and isinstance(medication_dict["end_date"], datetime.date):
        medication_dict["end_date"] = datetime.datetime.combine(medication_dict["end_date"], datetime.time.min)

    # Insert into the database
    result = await db["medications"].insert_one(medication_dict)
    new_medication = await db["medications"].find_one({"_id": result.inserted_id})

    # Convert Mongo _id to string for response
    new_medication["id"] = str(new_medication["_id"])
    del new_medication["_id"]
    
    return new_medication

async def get_all_medications(db):
    medications = []
    cursor = db["medications"].find()
    async for record in cursor:
        record["id"] = str(record["_id"])
        del record["_id"]
        medications.append(record)
    return medications


async def get_medications_by_resident(db, resident_id: str):
    if not ObjectId.is_valid(resident_id):
        raise HTTPException(status_code=400, detail="Invalid resident ID")
    
    medications = []
    cursor = db["medications"].find({"resident_id": resident_id})
    async for record in cursor:
        record["id"] = str(record["_id"])
        del record["_id"]
        medications.append(record)
    return medications


async def get_medication_by_id(db, resident_id: str, medication_id: str):
    if not ObjectId.is_valid(medication_id):
        raise HTTPException(status_code=400, detail="Invalid medication ID")
    
    record = await db["medications"].find_one({"_id": ObjectId(medication_id)})
    if not record:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    record["id"] = str(record["_id"])
    del record["_id"]
    return record


async def update_medication(db, resident_id: str, medication_id: str, update_data: MedicationCreate):
    if not ObjectId.is_valid(medication_id):
        raise HTTPException(status_code=400, detail="Invalid medication ID")
    
    update_dict = update_data.dict(exclude_unset=True)
    
    # Convert date fields to datetime
    for date_field in ["start_date", "end_date"]:
        if date_field in update_dict and update_dict[date_field]:
            if isinstance(update_dict[date_field], datetime.date):  # Ensure conversion
                update_dict[date_field] = datetime.datetime.combine(update_dict[date_field], datetime.time.min)

    
    result = await db["medications"].update_one(
        {"_id": ObjectId(medication_id)},
        {"$set": update_dict}
    )

    if result.modified_count == 0:
        record = await db["medications"].find_one({"_id": ObjectId(medication_id)})
        if not record:
            raise HTTPException(status_code=404, detail="Medication not found")

    updated_record = await db["medications"].find_one({"_id": ObjectId(medication_id)})
    updated_record["id"] = str(updated_record["_id"])
    del updated_record["_id"]
    return updated_record


async def delete_medication(db, resident_id: str, medication_id: str):
    if not ObjectId.is_valid(medication_id):
        raise HTTPException(status_code=400, detail="Invalid medication ID")
    
    result = await db["medications"].delete_one({"_id": ObjectId(medication_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Medication not found")

    return {"message": "Medication record deleted successfully"}
