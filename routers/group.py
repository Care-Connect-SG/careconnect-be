from typing import Dict, List

from fastapi import APIRouter, Depends, Request

from db.connection import get_db
from models.group import GroupCreate, GroupResponse
from services.group_service import (
    add_user_to_group,
    create_group,
    delete_group,
    get_all_groups,
    get_group_by_id,
    get_user_groups,
    remove_user_from_group,
    search_group,
    update_group,
)
from services.user_service import require_roles
from utils.limiter import limiter

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("/create", response_model=GroupResponse, response_model_by_alias=False)
@limiter.limit("10/minute")
async def create_new_group(
    request: Request,
    group_data: GroupCreate,
    db=Depends(get_db),
    current_user: Dict = Depends(require_roles(["Admin"])),
):
    return await create_group(db, group_data)


@router.post("/add-user")
@limiter.limit("10/minute")
async def add_user(
    request: Request,
    group_id: str,
    user_id: str,
    db=Depends(get_db),
    current_user: Dict = Depends(require_roles(["Admin"])),
):
    return await add_user_to_group(db, group_id, user_id)


@router.get("/", response_model=List[GroupResponse], response_model_by_alias=False)
@limiter.limit("100/minute")
async def get_groups(
    request: Request,
    db=Depends(get_db),
    user: dict = Depends(require_roles(["Admin", "Nurse"])),
):
    if user.get("role") != "Admin":
        return await get_user_groups(db, user.get("id"))
    return await get_all_groups(db)


@router.get("/{group_id}", response_model=GroupResponse, response_model_by_alias=False)
@limiter.limit("100/minute")
async def get_group_by_id_route(
    request: Request,
    group_id: str,
    db=Depends(get_db),
    user: dict = Depends(require_roles(["Admin", "Nurse"])),
):
    if user.get("role") != "Admin":
        return await get_group_by_id(db, group_id, user)
    return await get_group_by_id(db, group_id)


@router.put("/edit", response_model=GroupResponse, response_model_by_alias=False)
@limiter.limit("10/minute")
async def edit_group(
    request: Request,
    group_id: str,
    new_name: str,
    new_description: str,
    db=Depends(get_db),
    current_user: Dict = Depends(require_roles(["Admin"])),
):
    return await update_group(db, group_id, new_name, new_description)


@router.delete("/delete")
@limiter.limit("10/minute")
async def delete_group_route(
    request: Request,
    group_id: str,
    db=Depends(get_db),
    current_user: Dict = Depends(require_roles(["Admin"])),
):
    return await delete_group(db, group_id)


@router.delete("/remove-user")
@limiter.limit("10/minute")
async def remove_user(
    request: Request,
    group_id: str,
    user_id: str,
    db=Depends(get_db),
    current_user: Dict = Depends(require_roles(["Admin"])),
):
    return await remove_user_from_group(db, group_id, user_id)


@router.get("/search", response_model=GroupResponse, response_model_by_alias=False)
@limiter.limit("100/minute")
async def search_group_route(
    request: Request,
    group_id: str = None,
    name: str = None,
    db=Depends(get_db),
):
    return await search_group(db, group_id, name)


@router.get("/user-groups", response_model=List[GroupResponse])
@limiter.limit("100/minute")
async def search_user_groups(
    request: Request,
    user_id: str,
    db=Depends(get_db),
    current_user: Dict = Depends(require_roles(["Admin"])),
):
    return await get_user_groups(db, user_id)
