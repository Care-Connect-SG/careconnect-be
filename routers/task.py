import io
from fastapi import Depends, APIRouter, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from db.connection import get_db
from models.task import TaskCreate, TaskResponse, TaskUpdate
from services.ai.ai_task_service import get_ai_task_suggestion
from services.task_service import (
    accept_task_reassignment,
    complete_task,
    create_task,
    delete_task,
    download_task,
    download_tasks,
    duplicate_task,
    get_task_by_id,
    get_tasks,
    handle_task_self,
    reassign_task,
    reject_task_reassignment,
    reopen_task,
    request_task_reassignment,
    update_task,
)
from services.user_service import get_current_user, require_roles
from utils.limiter import limiter
from services.user_service import require_roles, get_current_user
from typing import Optional, List
from fastapi.responses import StreamingResponse
from datetime import datetime

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
# @limiter.limit("100/minute")
async def fetch_tasks(
    request: Request,
    search: Optional[str] = None,
    nurses: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    date: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(require_roles(["Admin", "Nurse"])),
):
    user_id = user.get("id")
    user_role = user.get("role")

    assigned_to = None
    if user_role == "Admin" and nurses and nurses != "undefined":
        assigned_to = nurses

    tasks = await get_tasks(
        db=db,
        assigned_to=assigned_to,
        status=status,
        priority=priority,
        category=category,
        search=search,
        date=date,
        user_role=user_role,
        user_id=user_id,
    )

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
    request: Request,
    task_id: str,
    delete_series: bool = False,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await delete_task(db, task_id, delete_series)
    return {"detail": "Task deleted successfully", "result": result}


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


@router.post(
    "/{task_id}/duplicate",
    summary="Duplicate a task",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("10/minute")
async def duplicate_task_route(
    request: Request,
    task_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    duplicated_task = await duplicate_task(db, task_id)
    return duplicated_task


@router.get(
    "/{task_id}/download",
    summary="Download a task as text or PDF file",
    response_class=StreamingResponse,
)
@limiter.limit("10/minute")
async def download_task_route(
    request: Request,
    task_id: str,
    format: str = "text",
    db: AsyncIOMotorDatabase = Depends(get_db),
):

    content = await download_task(db, task_id, format)

    if format == "text":
        media_type = "text/plain"
        filename = f"task-{task_id}.txt"
    elif format == "pdf":
        media_type = "application/pdf"
        filename = f"task-{task_id}.pdf"

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    return StreamingResponse(iter([content]), media_type=media_type, headers=headers)


@router.post(
    "/{task_id}/request-reassignment",
    summary="Request task reassignment to another nurse",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("10/minute")
async def request_reassignment(
    request: Request,
    task_id: str,
    target_nurse_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updated_task = await request_task_reassignment(
        db, task_id, target_nurse_id, current_user["id"]
    )
    return updated_task


@router.post(
    "/{task_id}/accept-reassignment",
    summary="Accept a task reassignment request",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("10/minute")
async def accept_reassignment(
    request: Request,
    task_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updated_task = await accept_task_reassignment(db, task_id, current_user["id"])
    return updated_task


@router.post(
    "/{task_id}/reject-reassignment",
    summary="Reject a task reassignment request",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("10/minute")
async def reject_reassignment(
    request: Request,
    task_id: str,
    rejection_reason: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updated_task = await reject_task_reassignment(
        db, task_id, current_user["id"], rejection_reason
    )
    return updated_task


@router.post(
    "/{task_id}/handle-self",
    summary="Handle the task yourself after rejection",
    response_model=TaskResponse,
    response_model_by_alias=False,
)
@limiter.limit("10/minute")
async def handle_task_self_route(
    request: Request,
    task_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    user: dict = Depends(require_roles(["Nurse"])),
):
    updated_task = await handle_task_self(db, task_id, current_user["id"])
    return updated_task


@router.get(
    "/ai-suggestion/{resident_id}",
    response_model=TaskCreate,
    response_model_by_alias=False,
)
async def get_task_suggestion(
    resident_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    suggestion = await get_ai_task_suggestion(db, resident_id, current_user)

    return suggestion


@router.post(
    "/download",
    summary="Download multiple tasks as a single PDF file",
    response_class=StreamingResponse,
)
@limiter.limit("10/minute")
async def download_tasks_route(
    request: Request,
    task_ids: List[str],
    db: AsyncIOMotorDatabase = Depends(get_db),
):

    content = await download_tasks(db, task_ids)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=tasks-{datetime.now().strftime('%Y%m%d')}.pdf"
        },
    )
