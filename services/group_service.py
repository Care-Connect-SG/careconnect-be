from fastapi import HTTPException
from bson import ObjectId

async def create_group(db, group_data):
    # Check if the group name already exists
    existing_group = await db["groups"].find_one({"name": group_data.name})
    if existing_group:
        raise HTTPException(status_code=400, detail="Group name already exists")

    # Convert Pydantic model to dictionary and insert into DB
    group_object = {
        "name": group_data.name,
        "description": group_data.description,  # Store description
        "members": []  # Initialize an empty members list
    }
    await db["groups"].insert_one(group_object)
    
    return {"res": "Group created successfully"}

async def add_user_to_group(db, group_name: str, user_email: str):
    # Check if the group exists
    group = await db["groups"].find_one({"name": group_name})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Add user to the group
    if user_email in group["members"]:
        raise HTTPException(status_code=400, detail="User already in group")

    await db["groups"].update_one(
        {"name": group_name}, {"$push": {"members": user_email}}
    )

    return {"res": f"User {user_email} added to group {group_name}"}


async def get_all_groups(db):
    groups_cursor = db["groups"].find({})
    groups = []
    async for group in groups_cursor:
        group["_id"] = str(group["_id"])  # Convert ObjectId to string
        groups.append(group)
    return groups

