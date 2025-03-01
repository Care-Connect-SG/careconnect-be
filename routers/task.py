from fastapi import Depends, APIRouter, Request, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.connection import get_db
from models.task import TaskResponse, TaskCreate, TaskStatus
from services.task_service import (
    create_task,
    get_tasks,
    get_task_by_id,
    update_task,
    delete_task,
    search_tasks,
    update_task_status,
    reassign_task,
)
from .limiter import limiter
from typing import Optional, List

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "/search",
    summary="Search tasks with filters",
    response_model=List[TaskResponse],
    response_model_by_alias=False,
)
@limiter.limit("5/second")
async def search_for_tasks(
    request: Request,
    status_filter: Optional[TaskStatus] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    assigned_to: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    tasks = await search_tasks(db, status_filter, priority, category, assigned_to)
    return tasks


@router.post(
    "/",
    summary="Create a new task",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
@limiter.limit("1/second")
async def create_new_task(
    request: Request, task: TaskCreate, db: AsyncIOMotorDatabase = Depends(get_db)
):
    new_task = await create_task(db, task)
    return new_task


@router.get(
    "/",
    summary="Fetch all tasks",
    response_model=List[TaskResponse],
    response_model_by_alias=False,
)
@limiter.limit("5/second")
async def fetch_tasks(
    request: Request,
    assigned_to: Optional[str] = None,
    status_filter: Optional[TaskStatus] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    tasks = await get_tasks(db, assigned_to, status_filter, priority, category)
    return tasks


@router.get(
    "/{task_id}",
    summary="Fetch a task by its ID",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("5/second")
async def fetch_task_by_id(
    request: Request, task_id: str, db: AsyncIOMotorDatabase = Depends(get_db)
):
    task = await get_task_by_id(db, task_id)
    return task


@router.put(
    "/{task_id}",
    summary="Update a task completely",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("1/second")
async def modify_task(
    request: Request,
    task_id: str,
    task: TaskCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    updated_task = await update_task(db, task_id, task)
    return updated_task


@router.delete(
    "/{task_id}", summary="Delete a task", status_code=status.HTTP_204_NO_CONTENT
)
@limiter.limit("1/second")
async def remove_task(
    request: Request, task_id: str, db: AsyncIOMotorDatabase = Depends(get_db)
):
    result = await delete_task(db, task_id)
    return {"message": "Task deleted successfully", "result": result}


@router.patch(
    "/{task_id}/status",
    summary="Update task status",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("1/second")
async def modify_task_status(
    request: Request,
    task_id: str,
    new_status: TaskStatus,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    updated_task = await update_task_status(db, task_id, new_status)
    return updated_task


@router.patch(
    "/{task_id}/reassign", summary="Reassign a task", response_model=TaskResponse
)
@limiter.limit("1/second")
async def modify_task_assignment(
    request: Request,
    task_id: str,
    new_assigned_to: List[str],
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    updated_task = await reassign_task(db, task_id, new_assigned_to)
    return updated_task
