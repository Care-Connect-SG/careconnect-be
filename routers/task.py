from fastapi import Depends, APIRouter, Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.connection import get_db
from models.task import Task, TaskCreate, TaskStatus
from services.task_service import (
    create_task, get_tasks, get_task_by_id, update_task, delete_task,
    search_tasks, update_task_status, reassign_task, get_ai_suggested_tasks,
    generate_tasks_pdf
)
from .limiter import limiter
from typing import Optional, List

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Static routes
@router.get("/search", summary="Search tasks with filters")
async def search_for_tasks(
    request: Request,
    status: Optional[TaskStatus] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    assigned_to: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await search_tasks(db, status, priority, category, assigned_to)

@router.get("/ai_suggestions", summary="Fetch AI-suggested tasks")
async def fetch_ai_tasks(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await get_ai_suggested_tasks(db)

@router.get("/download", summary="Download tasks as a PDF report")
async def download_tasks_as_pdf(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await generate_tasks_pdf(db)

# Dynamic routes
@router.post("/", summary="Create a new task")
@limiter.limit("1/second")
async def create_new_task(request: Request, task: TaskCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await create_task(db, task)

@router.get("/", summary="Fetch all tasks")
async def fetch_tasks(
    request: Request,
    assigned_to: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await get_tasks(db, assigned_to, status, priority, category)

@router.get("/{task_id}", summary="Fetch a task by its ID")
async def fetch_task_by_id(request: Request, task_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", summary="Update a task completely")
@limiter.limit("1/second")
async def modify_task(request: Request, task_id: str, task: TaskCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await update_task(db, task_id, task)

@router.delete("/{task_id}", summary="Delete a task")
@limiter.limit("1/second")
async def remove_task(request: Request, task_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await delete_task(db, task_id)

@router.patch("/{task_id}/status", summary="Update task status")
async def modify_task_status(request: Request, task_id: str, new_status: TaskStatus, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await update_task_status(db, task_id, new_status)

@router.patch("/{task_id}/reassign", summary="Reassign a task")
async def modify_task_assignment(request: Request, task_id: str, new_assigned_to: List[str], db: AsyncIOMotorDatabase = Depends(get_db)):
    return await reassign_task(db, task_id, new_assigned_to)
