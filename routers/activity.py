from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional
from datetime import datetime

from models.activity import Activity, ActivityCreate, ActivityUpdate, ActivityFilter
from services.activity_service import (
    create_activity,
    list_activities,
    get_activity,
    update_activity,
    delete_activity
)
from db.connection import get_db

router = APIRouter(prefix="/api/activities", tags=["activities"])

@router.post("/", response_model=Activity)
async def create_activity_route(
    request: Request,
    activity: ActivityCreate
):
    db = await get_db(request)
    return await create_activity(db, activity)

@router.get("/", response_model=List[Activity])
async def list_activities_route(
    request: Request,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("start_time", regex="^(start_time|title|category)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$")
):
    db = await get_db(request)
    return await list_activities(
        db,
        start_date,
        end_date,
        category,
        tags,
        search,
        sort_by,
        sort_order
    )

@router.get("/{activity_id}", response_model=Activity)
async def get_activity_route(
    request: Request,
    activity_id: str
):
    db = await get_db(request)
    return await get_activity(db, activity_id)

@router.put("/{activity_id}", response_model=Activity)
async def update_activity_route(
    request: Request,
    activity_id: str,
    activity_update: ActivityUpdate
):
    db = await get_db(request)
    return await update_activity(db, activity_id, activity_update)

@router.delete("/{activity_id}")
async def delete_activity_route(
    request: Request,
    activity_id: str
):
    db = await get_db(request)
    return await delete_activity(db, activity_id) 