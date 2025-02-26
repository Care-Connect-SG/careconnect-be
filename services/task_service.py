from motor.motor_asyncio import AsyncIOMotorDatabase
from models.task import Task, TaskStatus, TaskCreate
from bson import ObjectId
from fastapi import HTTPException
from typing import Optional, List

# Create Task
async def create_task(db: AsyncIOMotorDatabase, task: TaskCreate):
    task_dict = task.dict(by_alias=True, exclude_none=True)
    task_dict["_id"] = ObjectId()  # Generate a new MongoDB ObjectId
    await db.tasks.insert_one(task_dict)
    return {"message": "Task created successfully", "task_id": str(task_dict["_id"])}

# Get All Tasks (With Filters)
async def get_tasks(db: AsyncIOMotorDatabase, assigned_to=None, status=None, priority=None, category=None):
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
    # Convert MongoDB _id to string and remove it from the returned dict
    for task in tasks:
        task["id"] = str(task["_id"])
        del task["_id"]
    return tasks

# Get Task by ID
async def get_task_by_id(db: AsyncIOMotorDatabase, task_id: str):
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if task:
        task["id"] = str(task["_id"])
        del task["_id"]
        return task
    return None

# Update Task
async def update_task(db: AsyncIOMotorDatabase, task_id: str, updated_task: Task):
    update_data = updated_task.dict(by_alias=True, exclude_none=True)
    result = await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    if result.modified_count:
        return {"message": "Task updated successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

# Delete Task
async def delete_task(db: AsyncIOMotorDatabase, task_id: str):
    result = await db.tasks.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count:
        return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

# Search Tasks
async def search_tasks(db: AsyncIOMotorDatabase, status=None, priority=None, category=None, assigned_to=None):
    filters = {k: v for k, v in {
        "status": status,
        "priority": priority,
        "category": category,
        "assigned_to": assigned_to
    }.items() if v}
    tasks = await db.tasks.find(filters).to_list(length=100)
    for task in tasks:
        task["id"] = str(task["_id"])
        del task["_id"]
    return tasks

# Update Task Status
async def update_task_status(db: AsyncIOMotorDatabase, task_id: str, new_status: TaskStatus):
    result = await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"status": new_status}})
    if result.modified_count:
        return {"message": "Task status updated successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

# Reassign Task
async def reassign_task(db: AsyncIOMotorDatabase, task_id: str, new_assigned_to: List[str]):
    result = await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"assigned_to": new_assigned_to}})
    if result.modified_count:
        return {"message": "Task reassigned successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

# AI-Generated Task Retrieval (Placeholder)
async def get_ai_suggested_tasks(db: AsyncIOMotorDatabase):
    return []  # Placeholder until AI logic is added

# Generate Tasks as PDF (Placeholder)
async def generate_tasks_pdf(db: AsyncIOMotorDatabase):
    return {"message": "PDF generation not implemented yet"}
