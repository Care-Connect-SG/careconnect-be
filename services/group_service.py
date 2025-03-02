from fastapi import Depends, HTTPException, status
from bson import ObjectId, errors
from services.user_service import check_permissions


async def create_group(db, group_data, role: str = Depends(check_permissions(["Admin"]))):
    # Generate a new group_id automatically.
    group_id = str(ObjectId())

    # Check if the group name already exists.
    existing_group = await db["groups"].find_one({"name": group_data.name})
    if existing_group:
        raise HTTPException(status_code=400, detail="Group name already exists")

    # Create the group object with the new group_id and other details.
    group_object = {
        "_id": ObjectId(group_id),  # Create a new ObjectId from the generated id.
        "name": group_data.name,
        "description": group_data.description,
        "members": []  # Initialize an empty members list.
    }

    # Insert the group into the database.
    await db["groups"].insert_one(group_object)

    # Convert MongoDB _id to a string and assign it to 'id'.
    group_object["id"] = str(group_object["_id"])
    del group_object["_id"]

    return group_object


async def add_user_to_group(
    db,
    group_id: str,  # Now expecting a group_id (string) instead of group_name
    user_email: str,
    role: str = Depends(check_permissions(["Admin"]))
):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id format")

    # Find the group by its ObjectId.
    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if the user is already in the group.
    if user_email in group.get("members", []):
        raise HTTPException(status_code=400, detail="User already in group")

    # Add the user to the group's members list.
    await db["groups"].update_one({"_id": oid}, {"$push": {"members": user_email}})

    return {"res": f"User {user_email} added to group with id {group_id}"}


async def get_all_groups(db, role: str = Depends(check_permissions(["Admin"]))):
    groups_cursor = db["groups"].find({})
    groups = []
    async for group in groups_cursor:
        group["_id"] = str(group["_id"])  # Convert ObjectId to string
        groups.append(group)
    return groups


async def update_group(
    db,
    group_id: str,  # Use group_id instead of group_name
    new_name: str,
    new_description: str,
    role: str = Depends(check_permissions(["Admin"]))
):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id")

    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    updated_fields = {"name": new_name, "description": new_description}

    # Update the group document by its ObjectId.
    result = await db["groups"].update_one({"_id": oid}, {"$set": updated_fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found for update")
    # Do not throw error if modified_count is 0, because that might mean no changes were made.
    
    # Retrieve the updated document
    updated_group = await db["groups"].find_one({"_id": oid})
    if not updated_group:
        raise HTTPException(status_code=404, detail="Updated group not found")

    # Convert ObjectId to string and expose as 'id'
    updated_group["id"] = str(updated_group["_id"])
    del updated_group["_id"]

    return updated_group


async def delete_group(
    db, 
    group_id: str, 
    role: str = Depends(check_permissions(["Admin"]))
):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id")
    
    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Delete the group from the database using its _id.
    await db["groups"].delete_one({"_id": oid})

    return {"res": f"Group {group_id} deleted successfully"}


async def remove_user_from_group(
    db,
    group_id: str,  # Now expecting a group_id instead of group_name
    user_email: str,
    role: str = Depends(check_permissions(["Admin"]))
):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id format")

    # Find the group using its ObjectId.
    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if the user is part of the group.
    if user_email not in group.get("members", []):
        raise HTTPException(status_code=404, detail="User not found in group")

    # Remove the user from the group.
    await db["groups"].update_one({"_id": oid}, {"$pull": {"members": user_email}})

    return {"res": f"User {user_email} removed from group {group_id}"}


async def search_group(
    db,
    group_id: str = None,
    name: str = None,
    role: str = Depends(check_permissions(["Admin"]))
):
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

    # Convert ObjectId to string and assign to 'id'
    group["id"] = str(group["_id"])
    del group["_id"]
    return group

async def get_user_groups(
    db, user_email: str, role: str = Depends(check_permissions(["Admin"]))
):
    # Check if the user exists
    user = await db["users"].find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Find all groups where the user is a member
    groups_cursor = db["groups"].find({"members": user_email})
    groups = []
    async for group in groups_cursor:
        # Convert the MongoDB ObjectId to a string and assign it to 'id'
        group["id"] = str(group["_id"])
        del group["_id"]
        groups.append(group)

    return groups

