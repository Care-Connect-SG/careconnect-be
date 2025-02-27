from fastapi import APIRouter, Depends
from db.connection import get_db
from models.group import GroupCreate
from services.group_service import create_group, add_user_to_group, get_all_groups, update_group

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.post("/create")
async def create_new_group(group_data: GroupCreate, db=Depends(get_db)):
    return await create_group(db, group_data)

@router.post("/add-user")
async def add_user(group_name: str, user_email: str, db=Depends(get_db)):
    return await add_user_to_group(db, group_name, user_email)

@router.get("/")
async def list_groups(db=Depends(get_db)):
    return await get_all_groups(db)

@router.put("/edit")
async def edit_group(
    group_name: str, 
    new_name: str, 
    new_description: str, 
    db=Depends(get_db)
):
    return await update_group(db, group_name, new_name, new_description)
