from motor.motor_asyncio import AsyncIOMotorDatabase
from models.task import TaskStatus, TaskCreate, TaskResponse, TaskUpdate
from bson import ObjectId
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from services.resident_service import get_resident_full_name, get_resident_room
from services.user_service import get_assigned_to_name
from dateutil.relativedelta import relativedelta


# Create Task
async def create_task(
    db, task_data: TaskCreate, current_user: dict, single_mode: bool = False
) -> List[TaskResponse]:
    if (
        not single_mode
        and task_data.recurring
        and task_data.start_date
        and task_data.end_recurring_date
    ):
        return await create_recurring_task(db, task_data, current_user)

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


# Create Recurring Task
async def create_recurring_task(
    db, task_data: TaskCreate, current_user: dict
) -> List[TaskResponse]:
    tasks_created = []

    # Validate required recurring fields.
    if (
        not task_data.recurring
        or not task_data.start_date
        or not task_data.end_recurring_date
    ):
        raise ValueError(
            "Recurring task must have 'recurring', 'start_date', and 'end_recurring_date' set."
        )

    recurrence = task_data.recurring
    current_start_date = task_data.start_date
    current_due_date = (
        task_data.due_date if task_data.due_date else task_data.start_date
    )

    # Convert end_recurring_date (a date) into a datetime with timezone info.
    # Set it to the end of the day (23:59:59) to include all tasks on that day
    end_recurring_datetime = datetime.combine(
        task_data.end_recurring_date, datetime.max.time(), tzinfo=timezone.utc
    )

    # Use provided series_id or generate a new one
    series_id = (
        task_data.series_id
        if hasattr(task_data, "series_id") and task_data.series_id
        else str(ObjectId())
    )

    while current_start_date <= end_recurring_datetime:
        occurrence_task_data = task_data.copy(deep=True)
        occurrence_task_data.start_date = current_start_date
        occurrence_task_data.due_date = current_due_date
        occurrence_task_data.end_recurring_date = None
        occurrence_task_data.series_id = series_id  # series_id for grouping

        occurrence_tasks = await create_task(db, occurrence_task_data, current_user)
        tasks_created.extend(occurrence_tasks)

        # Increment dates based on recurrence type.
        if recurrence == "Daily":
            current_start_date += timedelta(days=1)
            current_due_date += timedelta(days=1)
        elif recurrence == "Weekly":
            current_start_date += timedelta(weeks=1)
            current_due_date += timedelta(weeks=1)
        elif recurrence == "Monthly":
            if relativedelta:
                current_start_date += relativedelta(months=1)
                current_due_date += relativedelta(months=1)
            else:
                new_month = current_start_date.month % 12 + 1
                new_year = current_start_date.year + (current_start_date.month // 12)
                current_start_date = current_start_date.replace(
                    year=new_year, month=new_month
                )
                if task_data.due_date:
                    new_month = current_due_date.month % 12 + 1
                    new_year = current_due_date.year + (current_due_date.month // 12)
                    current_due_date = current_due_date.replace(
                        year=new_year, month=new_month
                    )
        elif recurrence == "Annually":
            if relativedelta:
                current_start_date += relativedelta(years=1)
                current_due_date += relativedelta(years=1)
            else:
                current_start_date = current_start_date.replace(
                    year=current_start_date.year + 1
                )
                if task_data.due_date:
                    current_due_date = current_due_date.replace(
                        year=current_due_date.year + 1
                    )
        else:
            break

    return tasks_created


# Get All Tasks (With Filters)
async def get_tasks(
    db: AsyncIOMotorDatabase,
    assigned_to: str = None,
    status: str = None,
    priority: str = None,
    category: str = None,
    search: str = None,
    date: str = None,
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
            {"task_title": {"$regex": search, "$options": "i"}},
            {"task_details": {"$regex": search, "$options": "i"}},
        ]

    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD."
            )
        start_of_day = datetime.combine(
            date_obj, datetime.min.time(), tzinfo=timezone.utc
        )
        end_of_day = datetime.combine(
            date_obj, datetime.max.time(), tzinfo=timezone.utc
        )
    else:
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    filters["start_date"] = {"$gte": start_of_day, "$lte": end_of_day}

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
    db: AsyncIOMotorDatabase, task_id: str, updated_task: TaskUpdate
) -> TaskResponse:
    # Find the existing task by its _id.
    existing_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = updated_task.model_dump(by_alias=True, exclude_none=True)

    # Check if the update_series flag is present and true.
    if update_data.get("update_series"):
        update_data.pop("update_series")
        series_id = existing_task.get("series_id")
        if series_id:
            # Separate date-related fields from other fields
            date_fields = {}
            non_date_fields = {}

            for field, value in update_data.items():
                if field in [
                    "start_date",
                    "due_date",
                    "end_recurring_date",
                    "recurring",
                ]:
                    date_fields[field] = value
                else:
                    non_date_fields[field] = value

            # Ensure all dates are in UTC
            if "start_date" in date_fields:
                date_fields["start_date"] = date_fields["start_date"].replace(
                    tzinfo=timezone.utc
                )
            if "due_date" in date_fields:
                date_fields["due_date"] = date_fields["due_date"].replace(
                    tzinfo=timezone.utc
                )
            if "end_recurring_date" in date_fields:
                date_fields["end_recurring_date"] = date_fields[
                    "end_recurring_date"
                ].replace(tzinfo=timezone.utc)

            # Update non-date fields for all tasks in the series
            if non_date_fields:
                result = await db.tasks.update_many(
                    {"series_id": series_id}, {"$set": non_date_fields}
                )
                if result.matched_count == 0:
                    raise HTTPException(
                        status_code=404, detail="No tasks found for the series"
                    )

            # Update date fields only for the current task
            if date_fields:
                result = await db.tasks.update_one(
                    {"_id": ObjectId(task_id)}, {"$set": date_fields}
                )

            # Retrieve the current task as the response
            updated_task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
            return TaskResponse(**updated_task_doc)

    # Single task update.
    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    # Retrieve the updated task
    updated_task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
    return TaskResponse(**updated_task_doc)


# Delete Task
async def delete_task(
    db: AsyncIOMotorDatabase, task_id: str, delete_series: bool = False
) -> dict:
    # Find the task first to check if it's part of a series
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if delete_series and task.get("series_id"):
        # Delete all tasks in the series
        result = await db.tasks.delete_many({"series_id": task["series_id"]})
        if result.deleted_count:
            return {
                "detail": f"Series deleted successfully. {result.deleted_count} tasks were deleted."
            }
        raise HTTPException(status_code=404, detail="No tasks found in the series")
    else:
        # Delete single task
        result = await db.tasks.delete_one({"_id": ObjectId(task_id)})
        if result.deleted_count:
            return {"detail": "Task deleted successfully"}
        raise HTTPException(status_code=404, detail="Task not found")


# Update Task Status to Delayed if Overdue
async def update_if_overdue(db, task: dict) -> dict:
    if task.get("due_date") and task.get("status") != TaskStatus.COMPLETED:
        now = datetime.now(timezone.utc)
        due_date = task["due_date"]
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

    if "reassignment_requested_to" in task and task["reassignment_requested_to"]:
        task["reassignment_requested_to_name"] = await get_assigned_to_name(
            db, str(task["reassignment_requested_to"])
        )
    else:
        task["reassignment_requested_to_name"] = "Unknown"

    if "reassignment_requested_by" in task and task["reassignment_requested_by"]:
        task["reassignment_requested_by_name"] = await get_assigned_to_name(
            db, str(task["reassignment_requested_by"])
        )
    else:
        task["reassignment_requested_by_name"] = "Unknown"

    return task


# Enrich Task with Room
async def enrich_task_with_room(db, task: dict) -> dict:
    if "resident" in task:
        task["resident_room"] = await get_resident_room(db, str(task["resident"]))
    else:
        task["resident_room"] = "Unknown"
    return task


# Duplicate Task
async def duplicate_task(db: AsyncIOMotorDatabase, task_id: str) -> TaskResponse:
    original_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not original_task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_copy = original_task.copy()

    task_copy.pop("_id", None)

    task_copy["task_title"] = f"{task_copy['task_title']} (Copy)"

    task_copy["created_at"] = datetime.now(timezone.utc)

    result = await db.tasks.insert_one(task_copy)

    new_task = await db.tasks.find_one({"_id": result.inserted_id})
    new_task = await enrich_task_with_names(db, new_task)
    new_task = await enrich_task_with_room(db, new_task)

    return TaskResponse(**new_task)


# Download Task
async def download_task(db: AsyncIOMotorDatabase, task_id: str) -> bytes:

    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_dict = task.model_dump()
    task_dict["created_at"] = task_dict["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    task_dict["due_date"] = task_dict["due_date"].strftime("%Y-%m-%d %H:%M:%S")
    finished_at = task_dict.get("finished_at")
    finished_at_text = (
        f"\nFinished At: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}"
        if finished_at
        else ""
    )

    text_content = f"""Task Details
=============

Title: {task_dict["task_title"]}
Details: {task_dict["task_details"]}
Status: {task_dict["status"]}
Priority: {task_dict["priority"]}
Category: {task_dict["category"]}
Assigned To: {task_dict["assigned_to_name"]}
Resident: {task_dict["resident_name"]} (Room {task_dict["resident_room"]})
Created At: {task_dict["created_at"]}
Due Date: {task_dict["due_date"]}{finished_at_text}
"""

    return text_content.encode("utf-8")


async def request_task_reassignment(
    db: AsyncIOMotorDatabase,
    task_id: str,
    target_nurse_id: str,
    requesting_nurse_id: str,
) -> TaskResponse:
    # Get the existing task
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify the requesting nurse is currently assigned to the task
    if str(task.get("assigned_to")) != requesting_nurse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the currently assigned nurse can request reassignment",
        )

    # Update task with reassignment request details
    update_data = {
        "status": TaskStatus.REASSIGNMENT_REQUESTED,
        "reassignment_requested_to": ObjectId(target_nurse_id),
        "reassignment_requested_by": ObjectId(requesting_nurse_id),
        "reassignment_requested_at": datetime.now(timezone.utc),
    }

    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get the updated task with enriched data
    updated_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    updated_task = await enrich_task_with_names(db, updated_task)
    updated_task = await enrich_task_with_room(db, updated_task)

    return TaskResponse(**updated_task)


async def accept_task_reassignment(
    db: AsyncIOMotorDatabase, task_id: str, accepting_nurse_id: str
) -> TaskResponse:
    # Get the existing task
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify the accepting nurse is the one requested
    if str(task.get("reassignment_requested_to")) != accepting_nurse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requested nurse can accept the reassignment",
        )

    # Update task with new assignment
    update_data = {
        "status": TaskStatus.ASSIGNED,
        "assigned_to": ObjectId(accepting_nurse_id),
        "reassignment_requested_to": None,
        "reassignment_requested_by": None,
        "reassignment_requested_at": None,
    }

    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get the updated task with enriched data
    updated_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    updated_task = await enrich_task_with_names(db, updated_task)
    updated_task = await enrich_task_with_room(db, updated_task)

    return TaskResponse(**updated_task)


async def reject_task_reassignment(
    db: AsyncIOMotorDatabase,
    task_id: str,
    rejecting_nurse_id: str,
    rejection_reason: str,
) -> TaskResponse:
    # Get the existing task
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify the rejecting nurse is the one requested
    if str(task.get("reassignment_requested_to")) != rejecting_nurse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requested nurse can reject the reassignment",
        )

    # Update task with rejection details but maintain original status
    update_data = {
        "reassignment_rejection_reason": rejection_reason,
        "reassignment_rejected_at": datetime.now(timezone.utc),
        "reassignment_requested_to": None,
        "reassignment_requested_by": None,
        "reassignment_requested_at": None,
    }

    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get the updated task with enriched data
    updated_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    updated_task = await enrich_task_with_names(db, updated_task)
    updated_task = await enrich_task_with_room(db, updated_task)

    return TaskResponse(**updated_task)


async def handle_task_self(
    db: AsyncIOMotorDatabase, task_id: str, nurse_id: str
) -> TaskResponse:
    # Get the existing task
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify the nurse is the original assignee
    if str(task.get("assigned_to")) != nurse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the original assignee can handle the task themselves",
        )

    # Update task to be handled by the original nurse
    update_data = {
        "status": TaskStatus.ASSIGNED,
        "reassignment_requested_to": None,
        "reassignment_requested_by": None,
        "reassignment_requested_at": None,
        "reassignment_rejection_reason": None,
        "reassignment_rejected_at": None,
    }

    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get the updated task with enriched data
    updated_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    updated_task = await enrich_task_with_names(db, updated_task)
    updated_task = await enrich_task_with_room(db, updated_task)

    return TaskResponse(**updated_task)
