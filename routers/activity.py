from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional
from datetime import datetime
from models.activity import Activity, ActivityCreate, ActivityUpdate, ActivityFilter
from services import activity_service
from services.user_service import get_current_user

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.post("/", response_model=Activity)
async def create_activity(
    activity: ActivityCreate,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    return await activity_service.create_activity(activity, current_user["id"], request)


@router.get("/", response_model=List[Activity])
async def list_activities(
    request: Request,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("start_time", regex="^(start_time|title|category)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
):
    return await activity_service.get_activities(
        request=request,
        start_date=start_date,
        end_date=end_date,
        category=category,
        tags=tags,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/{activity_id}", response_model=Activity)
async def get_activity(activity_id: str, request: Request):
    return await activity_service.get_activity_by_id(activity_id, request)


@router.put("/{activity_id}", response_model=Activity)
async def update_activity(
    activity_id: str,
    activity_update: ActivityUpdate,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    return await activity_service.update_activity(activity_id, activity_update, current_user["id"], request)


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    return await activity_service.delete_activity(activity_id, current_user["id"], request)
