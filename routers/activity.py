from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from models.activity import Activity, ActivityCreate, ActivityUpdate, ActivityFilter
from db.connection import get_db

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.post("/", response_model=Activity)
async def create_activity(request: Request, activity: ActivityCreate):
    db = await get_db(request)
    activity_dict = activity.model_dump()
    activity_dict["created_by"] = "temp_user"  # Temporary user ID
    activity_dict["created_at"] = datetime.utcnow()
    activity_dict["updated_at"] = datetime.utcnow()

    result = await db.activities.insert_one(activity_dict)
    created_activity = await db.activities.find_one({"_id": result.inserted_id})
    return created_activity


@router.get("/", response_model=List[Activity])
async def list_activities(
    request: Request,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("start_time", regex="^(start_time|title|category)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
):
    db = await get_db(request)
    query = {}

    if start_date:
        query["start_time"] = {"$gte": start_date}
    if end_date:
        query["end_time"] = {"$lte": end_date}
    if category:
        query["category"] = category
    if tags:
        query["tags"] = {"$regex": tags}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    sort_direction = 1 if sort_order == "asc" else -1
    cursor = db.activities.find(query).sort(sort_by, sort_direction)
    activities = await cursor.to_list(length=None)
    return activities


@router.get("/{activity_id}", response_model=Activity)
async def get_activity(request: Request, activity_id: str):
    db = await get_db(request)
    activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.put("/{activity_id}", response_model=Activity)
async def update_activity(
    request: Request, activity_id: str, activity_update: ActivityUpdate
):
    db = await get_db(request)
    activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    update_data = activity_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    await db.activities.update_one(
        {"_id": ObjectId(activity_id)}, {"$set": update_data}
    )

    updated_activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
    return updated_activity


@router.delete("/{activity_id}")
async def delete_activity(request: Request, activity_id: str):
    db = await get_db(request)
    activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    await db.activities.delete_one({"_id": ObjectId(activity_id)})
    return {"message": "Activity deleted successfully"}
