from bson import ObjectId, errors
from fastapi import HTTPException

from models.group import GroupResponse


async def create_group(db, group_data):
    existing_group = await db["groups"].find_one({"name": group_data.name})
    if existing_group:
        raise HTTPException(status_code=400, detail="Group name already exists")

    members = []
    if group_data.members:
        for member_id in group_data.members:
            if ObjectId.is_valid(member_id):
                members.append(ObjectId(member_id))
            else:
                continue

    group_object = {
        "name": group_data.name,
        "description": group_data.description,
        "members": members,
    }

    result = await db["groups"].insert_one(group_object)
    created_group = await db["groups"].find_one({"_id": result.inserted_id})
    return GroupResponse(**created_group)


async def add_user_to_group(db, group_id: str, user_id: str):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id format")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user id format")

    user_obj_id = ObjectId(user_id)

    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    for member in group.get("members", []):
        if str(member) == str(user_obj_id):
            raise HTTPException(status_code=400, detail="User is already in the group")

    await db["groups"].update_one({"_id": oid}, {"$push": {"members": user_obj_id}})
    return {"res": f"User {user_id} added to group with id {group_id}"}


async def get_user_groups(db, user_id: str):
    try:
        uid = ObjectId(user_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id format")

    user = await db["users"].find_one({"_id": uid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    groups_cursor = db["groups"].find({"members": uid})
    groups = []
    async for group in groups_cursor:
        groups.append(GroupResponse(**group))

    return groups


async def get_all_groups(db):
    cursor = db["groups"].find({})
    groups = [GroupResponse(**group) async for group in cursor]
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
        user_id = user.get("id")
        if user.get("role") != "Admin":
            member_ids = [str(member) for member in group.get("members", [])]
            if user_id not in member_ids:
                raise HTTPException(
                    status_code=403, detail="Access forbidden to this group"
                )

    return GroupResponse(**group)


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

    return GroupResponse(**updated_group)


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

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user id format")

    user_obj_id = ObjectId(user_id)

    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user_in_group = False
    for member in group.get("members", []):
        if str(member) == str(user_obj_id):
            user_in_group = True
            break

    if not user_in_group:
        raise HTTPException(status_code=404, detail="User not found in group")

    await db["groups"].update_one({"_id": oid}, {"$pull": {"members": user_obj_id}})
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

    return GroupResponse(**group)
