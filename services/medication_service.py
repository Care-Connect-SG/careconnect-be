import datetime
from fastapi import HTTPException
from bson import ObjectId
from models.health_record.medication import MedicationCreate, MedicationResponse


async def create_medication(db, resident_id: str, medication_data: MedicationCreate):
    try:
        resident_oid = ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    medication_dict = medication_data.dict()
    medication_dict["resident_id"] = resident_id

    if "start_date" in medication_dict and isinstance(
        medication_dict["start_date"], datetime.date
    ):
        medication_dict["start_date"] = datetime.datetime.combine(
            medication_dict["start_date"], datetime.time.min
        )

    if "end_date" in medication_dict and isinstance(
        medication_dict["end_date"], datetime.date
    ):
        medication_dict["end_date"] = datetime.datetime.combine(
            medication_dict["end_date"], datetime.time.min
        )

    result = await db["medications"].insert_one(medication_dict)
    new_medication = await db["medications"].find_one({"_id": result.inserted_id})

    return MedicationResponse(**new_medication)


async def get_all_medications(db):
    medications = []
    cursor = db["medications"].find()
    async for record in cursor:
        medications.append(MedicationResponse(**record))

    return medications


async def get_medications_by_resident(db, resident_id: str):
    try:
        resident_oid = ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    medications = []
    cursor = db["medications"].find({"resident_id": resident_id})
    async for record in cursor:
        medications.append(MedicationResponse(**record))

    return medications


async def get_medication_by_id(db, resident_id: str, medication_id: str):
    try:
        medication_oid = ObjectId(medication_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid medication ID")

    record = await db["medications"].find_one({"_id": medication_oid})
    if not record:
        raise HTTPException(status_code=404, detail="Medication not found")

    return MedicationResponse(**record)


async def update_medication(
    db, resident_id: str, medication_id: str, update_data: MedicationCreate
):
    try:
        medication_oid = ObjectId(medication_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid medication ID")

    update_dict = update_data.dict(exclude_unset=True)
    for date_field in ["start_date", "end_date"]:
        if date_field in update_dict and update_dict[date_field]:
            if isinstance(update_dict[date_field], datetime.date):
                update_dict[date_field] = datetime.datetime.combine(
                    update_dict[date_field], datetime.time.min
                )

    result = await db["medications"].update_one(
        {"_id": medication_oid}, {"$set": update_dict}
    )

    if result.modified_count == 0:
        record = await db["medications"].find_one({"_id": medication_oid})
        if not record:
            raise HTTPException(status_code=404, detail="Medication not found")

    updated_record = await db["medications"].find_one({"_id": medication_oid})
    return MedicationResponse(**updated_record)


async def delete_medication(db, resident_id: str, medication_id: str):
    try:
        medication_oid = ObjectId(medication_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid medication ID")

    result = await db["medications"].delete_one({"_id": medication_oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Medication not found")

    return {"detail": "Medication record deleted successfully"}
