from fastapi import HTTPException
from datetime import datetime
from models.announcement import AnnouncementCreate

async def create_announcement(db, announcement_data: AnnouncementCreate):
    # Use the provided list of group names (ensure your AnnouncementCreate model has 'group_names')
    group_names = announcement_data.group_names

    # Retrieve the groups based on the provided names
    groups = await db["groups"].find({"name": {"$in": group_names}}).to_list(length=None)
    if len(groups) != len(group_names):
        raise HTTPException(status_code=404, detail="One or more groups not found")

    # Create the announcement object
    announcement_object = {
        "title": announcement_data.title,
        "message": announcement_data.message,
        "group_names": group_names,
        "created_at": datetime.utcnow(),
        "scheduled_time": announcement_data.scheduled_time
    }

    result = await db["announcements"].insert_one(announcement_object)
    # Convert ObjectId to string for response
    announcement_object["_id"] = str(result.inserted_id)

    return {"message": "Announcement created successfully", "announcement": announcement_object}

async def list_announcements_by_group(db, group_name: str):
    # Find announcements where the provided group_name is present in the "group_names" list
    announcements_cursor = db["announcements"].find({"group_names": group_name})
    announcements = []
    async for announcement in announcements_cursor:
        # Convert MongoDB _id to string and rename it to "id"
        announcement["id"] = str(announcement["_id"])
        del announcement["_id"]
        announcements.append(announcement)
    return announcements
