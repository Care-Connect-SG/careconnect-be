from fastapi import Depends, APIRouter, Request, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.connection import get_db
from models.task import Task, TaskStatus
from services.task_service import (
    create_task, get_tasks, get_task_by_id, update_task, delete_task,
    search_tasks, update_task_status, reassign_task, get_ai_suggested_tasks,
    generate_tasks_pdf
)
from .limiter import limiter
from typing import Optional, List

router = APIRouter(prefix="/tasks")

# Create a Task
@router.post("/")
@limiter.limit("1/second")
async def create_new_task(request: Request, task: Task, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await create_task(db, task)

# Get All Tasks
@router.get("/")
async def fetch_tasks(
    request: Request,
    assigned_to: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await get_tasks(db, assigned_to, status, priority, category)

# Get Task by ID
@router.get("/{task_id}")
async def fetch_task_by_id(request: Request, task_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Update Task (Full Update)
@router.put("/{task_id}")
@limiter.limit("1/second")
async def modify_task(request: Request, task_id: str, task: Task, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await update_task(db, task_id, task)

# Delete Task
@router.delete("/{task_id}")
@limiter.limit("1/second")
async def remove_task(request: Request, task_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await delete_task(db, task_id)

# Search Tasks by filters (Category, Priority, Assigned User, etc.)
@router.get("/search")
async def search_for_tasks(
    request: Request,
    status: Optional[TaskStatus] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    assigned_to: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await search_tasks(db, status, priority, category, assigned_to)

# Update Task Status
@router.patch("/{task_id}/status")
async def modify_task_status(request: Request, task_id: str, new_status: TaskStatus, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await update_task_status(db, task_id, new_status)

# Request and Approve Task Reassignment
@router.patch("/{task_id}/reassign")
async def modify_task_assignment(request: Request, task_id: str, new_assigned_to: List[str], db: AsyncIOMotorDatabase = Depends(get_db)):
    return await reassign_task(db, task_id, new_assigned_to)

# Get AI-Suggested Tasks
@router.get("/ai_suggestions")
async def fetch_ai_tasks(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await get_ai_suggested_tasks(db)

# Download Tasks as PDF Report
@router.get("/download")
async def download_tasks_as_pdf(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await generate_tasks_pdf(db)
