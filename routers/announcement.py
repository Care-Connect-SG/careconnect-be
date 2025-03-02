from fastapi import APIRouter, Depends
from db.connection import get_db
from models.announcement import AnnouncementCreate
from services.announcement_service import (
    create_announcement,
    list_announcements_by_group,
)

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.post("/create")
async def create_new_announcement(
    announcement_data: AnnouncementCreate, db=Depends(get_db)
):
    return await create_announcement(db, announcement_data)


@router.get("/group/{group_name}")
async def get_announcements_by_group(group_name: str, db=Depends(get_db)):
    return await list_announcements_by_group(db, group_name)
