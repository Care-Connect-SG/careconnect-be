from fastapi import Depends, HTTPException, status
from bson import ObjectId
from services.user_service import check_permissions


async def create_group(db, group_data, role: str = Depends(check_permissions(["Admin"]))):
    # Generate a group_id if one isn't provided
    group_id = group_data.group_id if group_data.group_id else str(ObjectId())

    # Check if the group name already exists
    existing_group = await db["groups"].find_one({"name": group_data.name})
    if existing_group:
        raise HTTPException(status_code=400, detail="Group name already exists")

    # Create the group object with the new group_id and other details
    group_object = {
        "_id": ObjectId(group_id),  # MongoDB ObjectId
        "name": group_data.name,
        "description": group_data.description,
        "members": []  # Initialize an empty members list
    }

    # Insert the group into the database
    await db["groups"].insert_one(group_object)

    # Convert MongoDB _id to a string and assign it to 'id'
    group_object["id"] = str(group_object["_id"])
    del group_object["_id"]

    return group_object



async def add_user_to_group(
    db,
    group_name: str,
    user_email: str,
    role: str = Depends(check_permissions(["Admin"])),
):
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


async def get_all_groups(db, role: str = Depends(check_permissions(["Admin"]))):
    groups_cursor = db["groups"].find({})
    groups = []
    async for group in groups_cursor:
        group["_id"] = str(group["_id"])  # Convert ObjectId to string
        groups.append(group)
    return groups


async def update_group(
    db,
    group_id: str,  # Now use group_id instead of group_name
    new_name: str,
    new_description: str,
    role: str = Depends(check_permissions(["Admin"])),
):
    try:
        oid = ObjectId(group_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid group id")

    group = await db["groups"].find_one({"_id": oid})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    updated_group = {"name": new_name, "description": new_description}

    # Update the group in the database by its ObjectId
    await db["groups"].update_one({"_id": oid}, {"$set": updated_group})

    return {"res": f"Group {group_id} updated successfully"}


async def delete_group(
    db, group_name: str, role: str = Depends(check_permissions(["Admin"]))
):
    # Check if the group exists
    group = await db["groups"].find_one({"name": group_name})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Delete the group from the database
    await db["groups"].delete_one({"name": group_name})

    return {"res": f"Group {group_name} deleted successfully"}


async def remove_user_from_group(
    db,
    group_name: str,
    user_email: str,
    role: str = Depends(check_permissions(["Admin"])),
):
    # Check if the group exists
    group = await db["groups"].find_one({"name": group_name})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if the user is part of the group
    if user_email not in group["members"]:
        raise HTTPException(status_code=404, detail="User not found in group")

    # Remove the user from the group
    await db["groups"].update_one(
        {"name": group_name}, {"$pull": {"members": user_email}}
    )

    return {"res": f"User {user_email} removed from group {group_name}"}


async def search_group(
    db,
    group_id: str = None,
    name: str = None,
    role: str = Depends(check_permissions(["Admin"])),
):
    query = {}
    if group_id:
        query["group_id"] = group_id
    elif name:
        query["name"] = name
    else:
        raise HTTPException(
            status_code=400, detail="Please provide either group_id or name"
        )

    group = await db["groups"].find_one(query)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group["_id"] = str(group["_id"])  # Convert ObjectId to string for serialization
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
    group_names = [group["name"] async for group in groups_cursor]

    # Return the list of group names
    return {"user_email": user_email, "groups": group_names}
