from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from db.mongodb import get_database
from models.activity import Activity, ActivityCreate


class ActivityService:
    collection_name = "activities"

    @classmethod
    async def create_activity(cls, activity: ActivityCreate) -> Activity:
        db = await get_database()
        activity_dict = activity.dict()
        activity_dict["created_at"] = datetime.utcnow()
        activity_dict["updated_at"] = datetime.utcnow()

        result = await db[cls.collection_name].insert_one(activity_dict)
        activity_dict["id"] = str(result.inserted_id)
        return Activity(**activity_dict)

    @classmethod
    async def get_activities(
        cls,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Activity]:
        db = await get_database()
        query = {}

        if start_date:
            query["start_date"] = {"$gte": start_date}
        if end_date:
            query["end_date"] = {"$lte": end_date}
        if category:
            query["category"] = category
        if location:
            query["location"] = location

        cursor = db[cls.collection_name].find(query)
        activities = await cursor.to_list(length=None)
        return [
            Activity(**{**activity, "id": str(activity["_id"])})
            for activity in activities
        ]

    @classmethod
    async def get_activity_by_id(cls, activity_id: str) -> Optional[Activity]:
        db = await get_database()
        activity = await db[cls.collection_name].find_one(
            {"_id": ObjectId(activity_id)}
        )
        if activity:
            return Activity(**{**activity, "id": str(activity["_id"])})
        return None

    @classmethod
    async def update_activity(
        cls, activity_id: str, activity: ActivityCreate
    ) -> Optional[Activity]:
        db = await get_database()
        activity_dict = activity.dict()
        activity_dict["updated_at"] = datetime.utcnow()

        result = await db[cls.collection_name].update_one(
            {"_id": ObjectId(activity_id)}, {"$set": activity_dict}
        )

        if result.modified_count:
            updated = await db[cls.collection_name].find_one(
                {"_id": ObjectId(activity_id)}
            )
            return Activity(**{**updated, "id": str(updated["_id"])})
        return None

    @classmethod
    async def delete_activity(cls, activity_id: str) -> bool:
        db = await get_database()
        result = await db[cls.collection_name].delete_one(
            {"_id": ObjectId(activity_id)}
        )
        return result.deleted_count > 0
