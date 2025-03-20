from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException
from db.mongodb import get_database
from models.activity import Activity, ActivityCreate, ActivityUpdate

async def create_activity(db, activity: ActivityCreate, user_id: str) -> Activity:
    try:
        activity_dict = activity.model_dump()
        activity_dict["created_by"] = user_id
        activity_dict["created_at"] = datetime.utcnow()
        activity_dict["updated_at"] = datetime.utcnow()
        
        result = await db.activities.insert_one(activity_dict)
        created_activity = await db.activities.find_one({"_id": result.inserted_id})
        return Activity(**created_activity)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create activity: {str(e)}")

async def list_activities(
    db,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "start_time",
    sort_order: str = "asc"
) -> List[Activity]:
    try:
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
                {"description": {"$regex": search, "$options": "i"}}
            ]

        sort_direction = 1 if sort_order == "asc" else -1
        cursor = db.activities.find(query).sort(sort_by, sort_direction)
        activities = await cursor.to_list(length=None)
        return [Activity(**activity) for activity in activities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list activities: {str(e)}")

async def get_activity(db, activity_id: str) -> Activity:
    try:
        activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        return Activity(**activity)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to get activity: {str(e)}")

async def update_activity(db, activity_id: str, activity_update: ActivityUpdate) -> Activity:
    try:
        activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        update_data = activity_update.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        await db.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {"$set": update_data}
        )
        
        updated_activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
        return Activity(**updated_activity)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to update activity: {str(e)}")

async def delete_activity(db, activity_id: str) -> dict:
    try:
        activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        await db.activities.delete_one({"_id": ObjectId(activity_id)})
        return {"message": "Activity deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to delete activity: {str(e)}") 