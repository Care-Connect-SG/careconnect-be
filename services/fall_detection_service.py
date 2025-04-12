from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from models.fall_detection import FallLogCreate, FallLogResponse

async def create_fall_log(db, log: FallLogCreate) -> FallLogResponse:
    log_dict = log.model_dump(exclude_unset=True)
    log_dict["timestamp"] = datetime.utcnow()

    result = await db["fall_logs"].insert_one(log_dict)
    new_record = await db["fall_logs"].find_one({"_id": result.inserted_id})
    return FallLogResponse(**new_record)


async def get_all_fall_logs(db) -> list[FallLogResponse]:
    logs = []
    cursor = db["fall_logs"].find()
    async for record in cursor:
        logs.append(FallLogResponse(**record))
    return logs


async def update_fall_log_status(db, fall_id: str, status: str) -> FallLogResponse:
    if not ObjectId.is_valid(fall_id):
        raise HTTPException(status_code=400, detail="Invalid fall log ID")

    await db["fall_logs"].update_one({"_id": ObjectId(fall_id)}, {"$set": {"status": status}})
    updated = await db["fall_logs"].find_one({"_id": ObjectId(fall_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Fall log not found")

    return FallLogResponse(**updated)
