from fastapi import HTTPException
from bson import ObjectId, errors


async def create_group(db, group_data):
    existing_group = await db["groups"].find_one({"name": group_data.name})
    if existing_group:
        raise HTTPException(status_code=400, detail="Group name already exists")

    group_object = {
        "name": group_data.name,
        "description": group_data.description,
        "members": group_data.members or [],
    }
    result = await db["groups"].insert_one(group_object)
    group_object["_id"] = result.inserted_id
    return group_object


async def add_user_to_group(db, group_id: str, user_id: str):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id format")
    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if user_id in group.get("members", []):
        raise HTTPException(status_code=400, detail="User is already in the group")
    await db["groups"].update_one({"_id": oid}, {"$push": {"members": user_id}})
    return {"res": f"User {user_id} added to group with id {group_id}"}


async def get_user_groups(db, user_id: str):
    try:
        uid = ObjectId(user_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id format")
    user = await db["users"].find_one({"_id": uid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    groups_cursor = db["groups"].find({"members": user_id})
    groups = []
    async for group in groups_cursor:
        groups.append(group)
    return groups


async def get_all_groups(db):
    cursor = db["groups"].find({})
    groups = [group async for group in cursor]
    return groups


async def get_group_by_id(db, group_id: str, user: dict = None):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id format")
    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if user:
        if user.get("role") != "Admin" and user.get("id") not in group.get(
            "members", []
        ):
            raise HTTPException(
                status_code=403, detail="Access forbidden to this group"
            )
    return group


async def update_group(db, group_id: str, new_name: str, new_description: str):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id")
    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    updated_fields = {"name": new_name, "description": new_description}
    result = await db["groups"].update_one({"_id": oid}, {"$set": updated_fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found for update")
    updated_group = await db["groups"].find_one({"_id": oid})
    if not updated_group:
        raise HTTPException(status_code=404, detail="Updated group not found")
    return updated_group


async def delete_group(db, group_id: str):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id")
    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db["groups"].delete_one({"_id": oid})
    return {"res": f"Group {group_id} deleted successfully"}


async def remove_user_from_group(db, group_id: str, user_id: str):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id format")
    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if user_id not in group.get("members", []):
        raise HTTPException(status_code=404, detail="User not found in group")
    await db["groups"].update_one({"_id": oid}, {"$pull": {"members": user_id}})
    return {"res": f"User {user_id} removed from group {group_id}"}


async def search_group(db, group_id: str = None, name: str = None):
    query = {}
    if group_id:
        try:
            query["_id"] = ObjectId(group_id)
        except errors.InvalidId:
            raise HTTPException(status_code=400, detail="Invalid group id format")
    elif name:
        query["name"] = name
    else:
        raise HTTPException(
            status_code=400, detail="Please provide either group_id or name"
        )
    group = await db["groups"].find_one(query)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


async def get_user_groups(db, user_id: str):
    try:
        uid = ObjectId(user_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id format")
    user = await db["users"].find_one({"_id": uid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    groups_cursor = db["groups"].find({"members": user_id})
    groups = []
    async for group in groups_cursor:
        groups.append(group)
    return groups
