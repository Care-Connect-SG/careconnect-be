from fastapi import APIRouter, Depends
from db.connection import get_db
from models.group import GroupCreate
from services.user_service import check_permissions
from services.group_service import create_group, add_user_to_group, get_all_groups, update_group, delete_group, remove_user_from_group, search_group, get_user_groups

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("/create")
async def create_new_group(
    group_data: GroupCreate,
    db=Depends(get_db)
):
    return await create_group(db, group_data)



@router.post("/add-user")
async def add_user(group_name: str, user_email: str, db=Depends(get_db)):
    return await add_user_to_group(db, group_name, user_email)


@router.get("/")
async def list_groups(db=Depends(get_db)):
    return await get_all_groups(db)

@router.put("/edit")
async def edit_group(
    group_id: str, 
    new_name: str, 
    new_description: str, 
    db=Depends(get_db)
):
    return await update_group(db, group_id, new_name, new_description)

@router.delete("/delete")
async def delete_group_route(
    group_name: str, 
    db=Depends(get_db)
):
    return await delete_group(db, group_name)

@router.delete("/remove-user")
async def remove_user_route(
    group_name: str, 
    user_email: str, 
    db=Depends(get_db)
):
    return await remove_user_from_group(db, group_name, user_email)

@router.get("/search")
async def search_group_route(
    group_id: str = None,  # Optional group_id parameter
    name: str = None,  # Optional name parameter
    db=Depends(get_db)
):
    return await search_group(db, group_id, name)

@router.get("/user-groups")
async def search_user_groups(user_email: str, db=Depends(get_db)):
    return await get_user_groups(db, user_email)
