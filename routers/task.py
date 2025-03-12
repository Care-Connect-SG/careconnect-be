from fastapi import Depends, APIRouter, Request, status, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.connection import get_db
from models.task import TaskResponse, TaskCreate, TaskUpdate, TaskStatus
from services.task_service import (
    create_task,
    get_tasks,
    get_task_by_id,
    update_task,
    delete_task,
    reassign_task,
    complete_task,
    reopen_task,
)
from utils.limiter import limiter
from services.user_service import require_roles, get_current_user
from typing import Optional, List

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "/",
    summary="Create a new task",
    response_model=List[TaskResponse],
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
@limiter.limit("10/minute")
async def create_new_task(
    request: Request,
    task: TaskCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    new_task = await create_task(db, task, current_user)
    return new_task


@router.get(
    "/",
    summary="Fetch all tasks",
    response_model=List[TaskResponse],
    response_model_by_alias=False,
)
@limiter.limit("100/minute")
async def fetch_tasks(
    request: Request,
    search: Optional[str] = None,
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(require_roles(["Admin", "Nurse"])),
):
    if user.get("role") != "Admin":
        assigned_to = user.get("id")
    tasks = await get_tasks(db, assigned_to, status, priority, category, search)
    return tasks


@router.get(
    "/{task_id}",
    summary="Fetch a task by its ID",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("100/minute")
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
@limiter.limit("10/minute")
async def modify_task(
    request: Request,
    task_id: str,
    task: TaskUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    updated_task = await update_task(db, task_id, task)
    return updated_task


@router.delete(
    "/{task_id}", summary="Delete a task", status_code=status.HTTP_204_NO_CONTENT
)
@limiter.limit("10/minute")
async def remove_task(
    request: Request, task_id: str, db: AsyncIOMotorDatabase = Depends(get_db)
):
    result = await delete_task(db, task_id)
    return {"message": "Task deleted successfully", "result": result}


@router.patch(
    "/{task_id}/reassign",
    summary="Reassign a task",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("10/minute")
async def modify_task_assignment(
    request: Request,
    task_id: str,
    new_assigned_to: List[str],
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    updated_task = await reassign_task(db, task_id, new_assigned_to)
    return updated_task


@router.patch(
    "/{task_id}/complete",
    summary="Mark a task as completed",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("10/minute")
async def complete_task_route(
    request: Request,
    task_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    completed_task = await complete_task(db, task_id)
    return completed_task


@router.patch(
    "/{task_id}/reopen",
    summary="Reopen a completed task",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("10/minute")
async def reopen_task_route(
    request: Request,
    task_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    reopened_task = await reopen_task(db, task_id)
    return reopened_task
