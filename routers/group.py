from fastapi import APIRouter, Depends, Request
from db.connection import get_db
from models.group import Group
from services.group_service import create_group, add_user_to_group, get_all_groups

router = APIRouter(prefix="/groups")

@router.post("/create")
async def create_new_group(request: Request, group: Group, db=Depends(get_db)):
    return await create_group(db, group)

@router.post("/{group_name}/add_user/{user_email}")
async def add_user(request: Request, group_name: str, user_email: str, db=Depends(get_db)):
    return await add_user_to_group(db, group_name, user_email)

@router.get("/")
async def list_groups(db=Depends(get_db)):
    return await get_all_groups(db)