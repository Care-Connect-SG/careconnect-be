from motor.motor_asyncio import AsyncIOMotorDatabase
from models.task import TaskStatus, TaskCreate, TaskResponse
from bson import ObjectId
from fastapi import HTTPException
from typing import List
from datetime import datetime, timezone


# Create Task
async def create_task(db: AsyncIOMotorDatabase, task: TaskCreate) -> TaskResponse:
    task_dict = task.model_dump(by_alias=True, exclude_none=True)
    task_dict["_id"] = ObjectId()
    await db.tasks.insert_one(task_dict)
    return TaskResponse(**task_dict)


# Get All Tasks (With Filters)
async def get_tasks(
    db: AsyncIOMotorDatabase,
    assigned_to: str = None,
    status: str = None,
    priority: str = None,
    category: str = None,
) -> List[TaskResponse]:
    filters = {}
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if category:
        filters["category"] = category

    tasks = await db.tasks.find(filters).to_list(length=100)
    return [TaskResponse(**task) for task in tasks]


# Get Task by ID
async def get_task_by_id(db: AsyncIOMotorDatabase, task_id: str) -> TaskResponse:
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if task:
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


# Search Tasks
async def search_tasks(
    db: AsyncIOMotorDatabase,
    status: str = None,
    priority: str = None,
    category: str = None,
    assigned_to: str = None,
) -> List[TaskResponse]:
    filters = {
        k: v
        for k, v in {
            "status": status,
            "priority": priority,
            "category": category,
            "assigned_to": assigned_to,
        }.items()
        if v
    }
    tasks = await db.tasks.find(filters).to_list(length=100)
    return [TaskResponse(**task) for task in tasks]


# Update Task Status
async def update_task_status(
    db: AsyncIOMotorDatabase, task_id: str, new_status: TaskStatus
) -> dict:
    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": {"status": new_status}}
    )
    if result.modified_count:
        return {"message": "Task status updated successfully"}
    raise HTTPException(status_code=404, detail="Task not found")


# Reassign Task
async def reassign_task(
    db: AsyncIOMotorDatabase, task_id: str, new_assigned_to: List[str]
) -> dict:
    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": {"assigned_to": new_assigned_to}}
    )
    if result.modified_count:
        return {"message": "Task reassigned successfully"}
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
