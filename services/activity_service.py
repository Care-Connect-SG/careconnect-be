from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException, Request

from db.connection import get_db
from models.activity import ActivityCreate, ActivityResponse, ActivityUpdate

collection_name = "activities"


async def create_activity(
    activity: ActivityCreate, user_id: str, request: Request
) -> ActivityResponse:
    try:
        db = await get_db(request)
        activity_dict = activity.model_dump(exclude_unset=True)
        activity_dict["created_by"] = ObjectId(user_id)
        activity_dict["created_at"] = datetime.now(timezone.utc)
        activity_dict["updated_at"] = datetime.now(timezone.utc)
        activity_dict["reminder_sent"] = False

        result = await db[collection_name].insert_one(activity_dict)
        created_activity = await db[collection_name].find_one(
            {"_id": result.inserted_id}
        )
        return ActivityResponse(**created_activity)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create activity: {str(e)}"
        )


async def get_activities(
    request: Request,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "start_time",
    sort_order: str = "asc",
    created_by: Optional[str] = None,
) -> List[ActivityResponse]:
    try:
        db = await get_db(request)
        query = {}

        if start_date and end_date:
            query["$and"] = [
                {"start_time": {"$lt": end_date}},
                {"end_time": {"$gt": start_date}},
            ]
        if category:
            query["category"] = category
        if tags:
            query["tags"] = {"$regex": tags}
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
            ]
        if created_by:
            query["created_by"] = ObjectId(created_by)

        sort_direction = 1 if sort_order == "asc" else -1
        cursor = db[collection_name].find(query).sort(sort_by, sort_direction)
        activities = await cursor.to_list(length=None)
        return [ActivityResponse(**activity) for activity in activities]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch activities: {str(e)}"
        )


async def get_activity_by_id(activity_id: str, request: Request) -> ActivityResponse:
    try:
        db = await get_db(request)
        activity = await db[collection_name].find_one({"_id": ObjectId(activity_id)})

        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        return ActivityResponse(**activity)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch activity: {str(e)}"
        )


async def update_activity(
    activity_id: str,
    activity_update: ActivityUpdate,
    current_user: dict,
    request: Request,
) -> ActivityResponse:
    try:
        db = await get_db(request)
        existing = await db[collection_name].find_one({"_id": ObjectId(activity_id)})

        if not existing:
            raise HTTPException(status_code=404, detail="Activity not found")

        user_id = None
        is_admin = False

        if isinstance(current_user, dict):
            user_id = current_user.get("id")
            is_admin = current_user.get("role") == "Admin"
        elif isinstance(current_user, str):
            user_id = current_user
        else:
            raise HTTPException(status_code=400, detail="Invalid user format")

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not provided")

        activity_creator_id = None
        if "created_by" in existing:
            activity_creator_id = str(existing["created_by"])

        user_id_str = str(user_id)

        if not is_admin and activity_creator_id != user_id_str:
            raise HTTPException(
                status_code=403, detail="Not authorized to update this activity"
            )

        update_data = activity_update.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["reminder_sent"] = False

        result = await db[collection_name].update_one(
            {"_id": ObjectId(activity_id)}, {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Activity update failed")

        updated = await db[collection_name].find_one({"_id": ObjectId(activity_id)})

        if not updated:
            raise HTTPException(status_code=404, detail="Activity not found")

        return ActivityResponse(**updated)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update activity: {str(e)}"
        )


async def delete_activity(
    activity_id: str, current_user: dict, request: Request
) -> bool:
    try:
        db = await get_db(request)
        existing = await db[collection_name].find_one({"_id": ObjectId(activity_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Activity not found")

        user_id = None
        is_admin = False

        if isinstance(current_user, dict):
            user_id = current_user.get("id")
            is_admin = current_user.get("role") == "Admin"
        elif isinstance(current_user, str):
            user_id = current_user
        else:
            raise HTTPException(status_code=400, detail="Invalid user format")

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not provided")

        activity_creator_id = None
        if "created_by" in existing:
            activity_creator_id = str(existing["created_by"])

        user_id_str = str(user_id)

        if not is_admin and activity_creator_id != user_id_str:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this activity"
            )

        result = await db[collection_name].delete_one({"_id": ObjectId(activity_id)})
        return result.deleted_count > 0
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Failed to delete activity: {str(e)}"
        )


async def mark_reminder_sent(activity_id: str, request: Request) -> ActivityResponse:
    try:
        db = await get_db(request)
        existing = await db[collection_name].find_one({"_id": ObjectId(activity_id)})

        if not existing:
            raise HTTPException(status_code=404, detail="Activity not found")

        await db[collection_name].update_one(
            {"_id": ObjectId(activity_id)},
            {"$set": {"reminder_sent": True, "updated_at": datetime.now(timezone.utc)}},
        )

        updated = await db[collection_name].find_one({"_id": ObjectId(activity_id)})
        return ActivityResponse(**updated)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to mark reminder as sent: {str(e)}"
        )
