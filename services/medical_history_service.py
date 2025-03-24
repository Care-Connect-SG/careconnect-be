import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from bson import ObjectId
from typing import List, Union, Dict, Type
from models.medical_history import (
    MedicalRecordType,
    ConditionRecord,
    AllergyRecord,
    ChronicIllnessRecord,
    SurgicalHistoryRecord,
    ImmunizationRecord,
    BaseMedicalRecord,
)

# Define a type that can be any of the medical record types
MedicalRecordUnion = Union[
    ConditionRecord,
    AllergyRecord,
    ChronicIllnessRecord,
    SurgicalHistoryRecord,
    ImmunizationRecord
]

# Mapping of record types to their corresponding models and collections
RECORD_TYPE_MAP: Dict[MedicalRecordType, Dict[str, Union[str, Type[BaseMedicalRecord]]]] = {
    MedicalRecordType.CONDITION: {"collection": "conditions", "model": ConditionRecord},
    MedicalRecordType.ALLERGY: {"collection": "allergies", "model": AllergyRecord},
    MedicalRecordType.CHRONIC_ILLNESS: {"collection": "chronic_illnesses", "model": ChronicIllnessRecord},
    MedicalRecordType.SURGICAL: {"collection": "surgical_history", "model": SurgicalHistoryRecord},
    MedicalRecordType.IMMUNIZATION: {"collection": "immunizations", "model": ImmunizationRecord},
}

async def create_medical_record(
    db: AsyncIOMotorDatabase,
    record_type: MedicalRecordType,
    resident_id: str,
    record_data: dict,
) -> MedicalRecordUnion:
    """Create a new medical record of the specified type"""
    try:
        # Get the appropriate model and collection
        record_info = RECORD_TYPE_MAP[record_type]
        model_class = record_info["model"]
        collection_name = record_info["collection"]

        # Add resident_id and timestamps to the record data
        record_data["resident_id"] = resident_id
        record_data["created_at"] = datetime.date.today()
        record_data["updated_at"] = datetime.date.today()

        # Validate the record data using the appropriate model
        try:
            record = model_class.parse_obj(record_data)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data for {record_type} record: {str(e)}"
            )

        # Convert dates to datetime for MongoDB
        insert_data = record.dict()
        for field, value in insert_data.items():
            if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
                insert_data[field] = datetime.datetime.combine(value, datetime.time.min)

        # Insert the record
        result = await db[collection_name].insert_one(insert_data)
        
        # Retrieve and return the created record
        new_record = await db[collection_name].find_one({"_id": result.inserted_id})
        if not new_record:
            raise HTTPException(status_code=500, detail="Failed to create medical record")
        
        new_record["_id"] = str(new_record["_id"])
        return model_class.parse_obj(new_record)

    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid record type: {record_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating medical record: {str(e)}")

async def update_medical_record(
    db: AsyncIOMotorDatabase,
    record_id: str,
    record_type: MedicalRecordType,
    resident_id: str,
    update_data: dict,
) -> MedicalRecordUnion:
    """Update an existing medical record"""
    try:
        if not ObjectId.is_valid(record_id):
            raise HTTPException(status_code=400, detail="Invalid record ID format")

        # Get the appropriate model and collection
        record_info = RECORD_TYPE_MAP[record_type]
        model_class = record_info["model"]
        collection_name = record_info["collection"]

        # Add resident_id and updated_at to the update data
        update_data["resident_id"] = resident_id
        update_data["updated_at"] = datetime.date.today()

        # Validate the update data
        try:
            record = model_class.parse_obj(update_data)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data for {record_type} record: {str(e)}"
            )

        # Convert dates to datetime for MongoDB
        update_dict = record.dict()
        for field, value in update_dict.items():
            if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
                update_dict[field] = datetime.datetime.combine(value, datetime.time.min)

        # Update the record
        result = await db[collection_name].update_one(
            {"_id": ObjectId(record_id), "resident_id": resident_id},
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No {record_type} record found with ID {record_id} for resident {resident_id}"
            )

        # Retrieve and return the updated record
        updated_record = await db[collection_name].find_one({"_id": ObjectId(record_id)})
        if not updated_record:
            raise HTTPException(status_code=404, detail="Record not found after update")

        updated_record["_id"] = str(updated_record["_id"])
        return model_class.parse_obj(updated_record)

    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid record type: {record_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating medical record: {str(e)}")

async def get_medical_records_by_resident(
    db: AsyncIOMotorDatabase,
    resident_id: str
) -> List[MedicalRecordUnion]:
    """Get all medical records for a resident with full details for each record type"""
    try:
        all_records = []
        
        # Iterate through all record types and collect records
        for record_type, info in RECORD_TYPE_MAP.items():
            collection_name = info["collection"]
            model_class = info["model"]
            
            async for record in db[collection_name].find({"resident_id": resident_id}):
                record["_id"] = str(record["_id"])
                all_records.append(model_class.parse_obj(record))

        return all_records

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching medical records: {str(e)}"
        )

async def delete_medical_record(
    db: AsyncIOMotorDatabase,
    record_id: str,
    record_type: MedicalRecordType,
    resident_id: str
) -> dict:
    """Delete a medical record"""
    try:
        if not ObjectId.is_valid(record_id):
            raise HTTPException(status_code=400, detail="Invalid record ID format")

        collection_name = RECORD_TYPE_MAP[record_type]["collection"]
        result = await db[collection_name].delete_one({
            "_id": ObjectId(record_id),
            "resident_id": resident_id
        })

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No {record_type} record found with ID {record_id} for resident {resident_id}"
            )

        return {"detail": f"{record_type} record successfully deleted"}

    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid record type: {record_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting medical record: {str(e)}")
