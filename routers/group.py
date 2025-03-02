from fastapi import APIRouter, Depends
from db.connection import get_db
from typing import List
from models.group import GroupCreate, GroupResponse
from services.user_service import check_permissions
from services.group_service import create_group, add_user_to_group, get_all_groups, update_group, delete_group, remove_user_from_group, search_group, get_user_groups

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("/create", response_model=GroupResponse,response_model_by_alias=False)
async def create_new_group(
    group_data: GroupCreate,
    db=Depends(get_db)
):
    return await create_group(db, group_data)



@router.post("/add-user")
async def add_user(group_id: str, user_email: str, db=Depends(get_db)):
    return await add_user_to_group(db, group_id, user_email)


@router.get("/", response_model=List[GroupResponse],response_model_by_alias=False)
async def list_groups(db=Depends(get_db)):
    return await get_all_groups(db)

@router.put("/edit", response_model=GroupResponse,response_model_by_alias=False)
async def edit_group(
    group_id: str, 
    new_name: str, 
    new_description: str, 
    db=Depends(get_db)
):
    return await update_group(db, group_id, new_name, new_description)

@router.delete("/delete")
async def delete_group_route(
    group_id: str, 
    db=Depends(get_db)
):
    return await delete_group(db, group_id)

@router.delete("/remove-user")
async def remove_user_route(
    group_id: str,  # Use group_id here instead of group_name
    user_email: str, 
    db=Depends(get_db)
):
    return await remove_user_from_group(db, group_id, user_email)

@router.get("/search", response_model=GroupResponse, response_model_by_alias=False)
async def search_group_route(
    group_id: str = None,  
    name: str = None,  # Optional name parameter
    db=Depends(get_db)
):
    return await search_group(db, group_id, name)

@router.get("/user-groups", response_model=List[GroupResponse])
async def search_user_groups(user_email: str, db=Depends(get_db)):
    return await get_user_groups(db, user_email)

