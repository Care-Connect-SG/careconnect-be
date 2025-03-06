from motor.motor_asyncio import AsyncIOMotorDatabase
from models.task import TaskStatus, TaskCreate, TaskResponse
from bson import ObjectId
from fastapi import HTTPException
from typing import List
from datetime import datetime, timezone
from services.resident_service import get_resident_full_name, get_resident_room
from services.user_service import get_assigned_to_name


# Create Task
async def create_task(
    db, task_data: TaskCreate, current_user: dict
) -> List[TaskResponse]:
    tasks_created = []
    for resident_id in task_data.residents:
        task_doc = task_data.model_dump(exclude={"residents"})
        task_doc["resident"] = ObjectId(resident_id)
        task_doc["created_by"] = ObjectId(current_user["id"])
        task_doc["created_at"] = datetime.now(timezone.utc)
        task_doc["assigned_to"] = ObjectId(task_data.assigned_to)
        result = await db.tasks.insert_one(task_doc)
        new_task = await db.tasks.find_one({"_id": result.inserted_id})
        tasks_created.append(TaskResponse(**new_task))
    return tasks_created


# Get All Tasks (With Filters)
async def get_tasks(
    db: AsyncIOMotorDatabase,
    assigned_to: str = None,
    status: str = None,
    priority: str = None,
    category: str = None,
    search: str = None,
) -> List[TaskResponse]:
    filters = {}
    if assigned_to:
        filters["assigned_to"] = ObjectId(assigned_to)
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if category:
        filters["category"] = category
    if search:
        filters["$or"] = [
            {"task_detail": {"$regex": search, "$options": "i"}},
            {"task_details": {"$regex": search, "$options": "i"}},
        ]

    # Currently it restricts results to tasks due today.
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    filters["due_date"] = {"$gte": start_of_day, "$lte": end_of_day}

    tasks = await db.tasks.find(filters).to_list(length=100)
    enriched_tasks = []
    for task in tasks:
        task = await update_if_overdue(db, task)
        task = await enrich_task_with_names(db, task)
        enriched_tasks.append(TaskResponse(**task))
    return enriched_tasks


# Get Task by ID
async def get_task_by_id(db: AsyncIOMotorDatabase, task_id: str) -> TaskResponse:
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if task:
        task = await update_if_overdue(db, task)
        task = await enrich_task_with_names(db, task)
        task = await enrich_task_with_room(db, task)
        return TaskResponse(**task)
    raise HTTPException(status_code=404, detail="Task not found")


# Update Task
async def update_task(
    db: AsyncIOMotorDatabase, task_id: str, updated_task: TaskCreate
) -> TaskResponse:
    update_data = updated_task.model_dump(by_alias=True, exclude_none=True)
    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": update_data}
    )
    if result.modified_count:
        updated_task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
        return TaskResponse(**updated_task_doc)
    raise HTTPException(status_code=404, detail="Task not found")


# Delete Task
async def delete_task(db: AsyncIOMotorDatabase, task_id: str) -> dict:
    result = await db.tasks.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count:
        return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")


# Update Task Status to Delayed if Overdue
async def update_if_overdue(db, task: dict) -> dict:
    if task.get("due_date") and task.get("status") != TaskStatus.COMPLETED:
        now = datetime.now(timezone.utc)
        due_date = task["due_date"]
        # If due_date is naive (no tzinfo), assume it is UTC and attach timezone info
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        if now > due_date:
            await db.tasks.update_one(
                {"_id": task["_id"]}, {"$set": {"status": TaskStatus.DELAYED}}
            )
            task["status"] = TaskStatus.DELAYED
    return task


# Reassign Task
async def reassign_task(
    db: AsyncIOMotorDatabase, task_id: str, new_assigned_to: List[str]
) -> TaskResponse:
    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": {"assigned_to": new_assigned_to}}
    )
    if result.modified_count:
        updated_task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
        return TaskResponse(**updated_task_doc)
    raise HTTPException(status_code=404, detail="Task not found")


# Complete Task
async def complete_task(db: AsyncIOMotorDatabase, task_id: str) -> TaskResponse:
    update_data = {
        "status": TaskStatus.COMPLETED,
        "finished_at": datetime.now(timezone.utc),
    }
    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": update_data}
    )
    if result.modified_count:
        updated_task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
        return TaskResponse(**updated_task_doc)
    raise HTTPException(status_code=404, detail="Task not found")


# Reopen Task
async def reopen_task(db: AsyncIOMotorDatabase, task_id: str) -> TaskResponse:
    task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task_doc:
        raise HTTPException(status_code=404, detail="Task not found")
    new_status = TaskStatus.ASSIGNED
    due_date = task_doc.get("due_date")
    if due_date:
        now = datetime.now(timezone.utc)
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        if now > due_date:
            new_status = TaskStatus.DELAYED
    update_data = {
        "status": new_status,
        "finished_at": None,
    }
    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": update_data}
    )
    if result.modified_count:
        updated_task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
        return TaskResponse(**updated_task_doc)
    raise HTTPException(status_code=404, detail="Task not found")


# Enrich Task with Names
async def enrich_task_with_names(db, task: dict) -> dict:
    if "assigned_to" in task:
        task["assigned_to_name"] = await get_assigned_to_name(
            db, str(task["assigned_to"])
        )
    else:
        task["assigned_to_name"] = "Unknown"

    if "resident" in task:
        task["resident_name"] = await get_resident_full_name(db, str(task["resident"]))
    else:
        task["resident_name"] = "Unknown"

    return task


# Enrich Task with Room
async def enrich_task_with_room(db, task: dict) -> dict:
    if "resident" in task:
        task["resident_room"] = await get_resident_room(db, str(task["resident"]))
    else:
        task["resident_room"] = "Unknown"
    return task
