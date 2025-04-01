from datetime import datetime, timedelta, timezone
from typing import List

from bson import ObjectId
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.task import TaskCreate, TaskResponse, TaskStatus, TaskUpdate
from services.group_service import get_user_groups
from services.resident_service import get_resident_full_name, get_resident_room
from services.user_service import get_assigned_to_name


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


async def create_recurring_task(
    db, task_data: TaskCreate, current_user: dict
) -> List[TaskResponse]:
    tasks_created = []

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

    end_recurring_datetime = datetime.combine(
        task_data.end_recurring_date, datetime.max.time(), tzinfo=timezone.utc
    )

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
        occurrence_task_data.series_id = series_id

        occurrence_tasks = await create_task(db, occurrence_task_data, current_user)
        tasks_created.extend(occurrence_tasks)

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


async def get_tasks(
    db: AsyncIOMotorDatabase,
    assigned_to: str = None,
    status: str = None,
    priority: str = None,
    category: str = None,
    search: str = None,
    date: str = None,
    user_role: str = None,
) -> List[TaskResponse]:
    filters = {}
    if user_role == "Admin":
        if assigned_to:
            if "," in assigned_to:
                try:
                    nurse_ids = [
                        ObjectId(id.strip())
                        for id in assigned_to.split(",")
                        if id.strip()
                    ]
                    if nurse_ids:
                        filters["assigned_to"] = {"$in": nurse_ids}
                except Exception as e:
                    raise Exception(f"Error processing nurse IDs: {e}")
            else:
                try:
                    filters["assigned_to"] = ObjectId(assigned_to)
                except Exception as e:
                    raise Exception(f"Error converting nurse ID to ObjectId: {e}")
    else:
        try:
            groups = await get_user_groups(db, assigned_to)

            group_member_ids = set()
            for group in groups:
                for member in group.members:
                    group_member_ids.add(str(member))

            group_member_ids.add(assigned_to)

            obj_ids = [
                ObjectId(id) for id in group_member_ids if id and id != "undefined"
            ]
            if obj_ids:
                filters["assigned_to"] = {"$in": obj_ids}

        except Exception as e:
            try:
                filters["assigned_to"] = ObjectId(assigned_to)
            except Exception as e2:
                raise Exception(f"Error converting user ID to ObjectId: {e2}")

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


async def get_task_by_id(db: AsyncIOMotorDatabase, task_id: str) -> TaskResponse:
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if task:
        task = await update_if_overdue(db, task)
        task = await enrich_task_with_names(db, task)
        task = await enrich_task_with_room(db, task)
        return TaskResponse(**task)
    raise HTTPException(status_code=404, detail="Task not found")


async def update_task(
    db: AsyncIOMotorDatabase, task_id: str, updated_task: TaskUpdate
) -> TaskResponse:
    existing_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = updated_task.model_dump(by_alias=True, exclude_none=True)

    if update_data.get("update_series"):
        update_data.pop("update_series")
        series_id = existing_task.get("series_id")
        if series_id:
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

            if non_date_fields:
                result = await db.tasks.update_many(
                    {"series_id": series_id}, {"$set": non_date_fields}
                )
                if result.matched_count == 0:
                    raise HTTPException(
                        status_code=404, detail="No tasks found for the series"
                    )

            if date_fields:
                result = await db.tasks.update_one(
                    {"_id": ObjectId(task_id)}, {"$set": date_fields}
                )

            tasks_in_series = await db.tasks.find({"series_id": series_id}).to_list(
                length=100
            )
            for task in tasks_in_series:
                await update_task_status(db, task)

            updated_task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
            return TaskResponse(**updated_task_doc)

    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)}, {"$set": update_data}
    )
    if result.modified_count == 0 and not update_data:
        updated_task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
    elif result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found or no changes made")
    else:
        updated_task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})

    if "status" not in update_data:
        updated_task_doc = await update_task_status(db, updated_task_doc)

    updated_task_doc = await enrich_task_with_names(db, updated_task_doc)
    return TaskResponse(**updated_task_doc)


async def delete_task(
    db: AsyncIOMotorDatabase, task_id: str, delete_series: bool = False
) -> dict:
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if delete_series and task.get("series_id"):
        result = await db.tasks.delete_many({"series_id": task["series_id"]})
        if result.deleted_count:
            return {
                "detail": f"Series deleted successfully. {result.deleted_count} tasks were deleted."
            }
        raise HTTPException(status_code=404, detail="No tasks found in the series")
    else:
        result = await db.tasks.delete_one({"_id": ObjectId(task_id)})
        if result.deleted_count:
            return {"detail": "Task deleted successfully"}
        raise HTTPException(status_code=404, detail="Task not found")


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


async def enrich_task_with_names(db, task: dict) -> dict:

    if "assigned_to" in task:
        task["assigned_to_name"] = await get_assigned_to_name(
            db, str(task["assigned_to"])
        )
    else:
        task["assigned_to_name"] = "Unknown"

    if "resident" in task:
        resident_db = db.client.get_database("resident")
        task["resident_name"] = await get_resident_full_name(
            resident_db, str(task["resident"])
        )
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


async def enrich_task_with_room(db, task: dict) -> dict:
    if "resident" in task:
        resident_db = db.client.get_database("resident")
        task["resident_room"] = await get_resident_room(
            resident_db, str(task["resident"])
        )
    else:
        task["resident_room"] = "Unknown"
    return task


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


async def download_task(
    db: AsyncIOMotorDatabase, task_id: str, format: str = "text"
) -> bytes:
    """Download a task in either text or PDF format."""
    task = await get_task_by_id(db, task_id)
    task_dict = task.model_dump()

    # Enrich task with names and room information
    task_dict = await enrich_task_with_names(db, task_dict)
    task_dict = await enrich_task_with_room(db, task_dict)

    if format == "text":
        content = [
            f"Task Details",
            f"============",
            f"Title: {task_dict['task_title']}",
            f"Status: {task_dict['status']}",
            f"Priority: {task_dict['priority']}",
            f"Category: {task_dict['category']}",
            f"Details: {task_dict['task_details']}",
            f"",
            f"Resident Information",
            f"===================",
            f"Name: {task_dict.get('resident_name', 'N/A')}",
            f"Room: {task_dict.get('resident_room', 'N/A')}",
            f"",
            f"Assignment Information",
            f"=====================",
            f"Assigned To: {task_dict.get('assigned_to_name', 'N/A')}",
            f"Start Date: {task_dict['start_date'].strftime('%Y-%m-%d %H:%M')}",
            f"Due Date: {task_dict['due_date'].strftime('%Y-%m-%d %H:%M') if task_dict.get('due_date') else 'N/A'}",
            f"",
            f"Additional Information",
            f"=====================",
            f"Created At: {task_dict['created_at'].strftime('%Y-%m-%d %H:%M')}",
            f"Last Updated: {task_dict.get('updated_at', 'N/A')}",
            f"Recurring: {task_dict.get('recurring', 'No')}",
            f"Series ID: {task_dict.get('series_id', 'N/A')}",
        ]
        return "\n".join(content).encode()
    elif format == "pdf":
        from io import BytesIO

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                        Table, TableStyle)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        styles = getSampleStyleSheet()

        # Create custom styles for the content
        title_style = ParagraphStyle(
            "CustomTitle", parent=styles["Heading1"], fontSize=16, spaceAfter=30
        )

        cell_style = ParagraphStyle(
            "CellStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,  # Line height
            wordWrap="CJK",  # Enable word wrapping
            splitLongWords=True,
        )

        header_style = ParagraphStyle(
            "HeaderStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.white,
            wordWrap="CJK",
        )

        story = []

        # Title
        story.append(Paragraph(f"Task Details: {task_dict['task_title']}", title_style))
        story.append(Spacer(1, 12))

        # Convert data to paragraphs for proper wrapping
        data = [
            [
                Paragraph("Status:", header_style),
                Paragraph(task_dict["status"], cell_style),
            ],
            [
                Paragraph("Priority:", header_style),
                Paragraph(task_dict["priority"], cell_style),
            ],
            [
                Paragraph("Category:", header_style),
                Paragraph(task_dict["category"], cell_style),
            ],
            [
                Paragraph("Details:", header_style),
                Paragraph(task_dict["task_details"], cell_style),
            ],
            [
                Paragraph("Resident:", header_style),
                Paragraph(task_dict.get("resident_name", "N/A"), cell_style),
            ],
            [
                Paragraph("Room:", header_style),
                Paragraph(task_dict.get("resident_room", "N/A"), cell_style),
            ],
            [
                Paragraph("Assigned To:", header_style),
                Paragraph(task_dict.get("assigned_to_name", "N/A"), cell_style),
            ],
            [
                Paragraph("Start Date:", header_style),
                Paragraph(
                    task_dict["start_date"].strftime("%Y-%m-%d %H:%M"), cell_style
                ),
            ],
            [
                Paragraph("Due Date:", header_style),
                Paragraph(
                    (
                        task_dict["due_date"].strftime("%Y-%m-%d %H:%M")
                        if task_dict.get("due_date")
                        else "N/A"
                    ),
                    cell_style,
                ),
            ],
            [
                Paragraph("Created At:", header_style),
                Paragraph(
                    task_dict["created_at"].strftime("%Y-%m-%d %H:%M"), cell_style
                ),
            ],
            [
                Paragraph("Last Updated:", header_style),
                Paragraph(str(task_dict.get("updated_at", "N/A")), cell_style),
            ],
            [
                Paragraph("Recurring:", header_style),
                Paragraph(str(task_dict.get("recurring", "No")), cell_style),
            ],
            [
                Paragraph("Series ID:", header_style),
                Paragraph(str(task_dict.get("series_id", "N/A")), cell_style),
            ],
        ]

        # Create table with auto-width columns
        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.blue),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),  # Align text to top of cells
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),  # Add left padding
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),  # Add right padding
                ]
            )
        )

        story.append(table)
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    else:
        raise ValueError("Invalid format. Must be either 'text' or 'pdf'")


async def request_task_reassignment(
    db: AsyncIOMotorDatabase,
    task_id: str,
    target_nurse_id: str,
    requesting_nurse_id: str,
) -> TaskResponse:
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if str(task.get("assigned_to")) != requesting_nurse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the currently assigned nurse can request reassignment",
        )

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

    updated_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    updated_task = await enrich_task_with_names(db, updated_task)
    updated_task = await enrich_task_with_room(db, updated_task)

    return TaskResponse(**updated_task)


async def accept_task_reassignment(
    db: AsyncIOMotorDatabase, task_id: str, accepting_nurse_id: str
) -> TaskResponse:
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if str(task.get("reassignment_requested_to")) != accepting_nurse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requested nurse can accept the reassignment",
        )

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
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if str(task.get("reassignment_requested_to")) != rejecting_nurse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requested nurse can reject the reassignment",
        )

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

    updated_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    updated_task = await enrich_task_with_names(db, updated_task)
    updated_task = await enrich_task_with_room(db, updated_task)

    return TaskResponse(**updated_task)


async def handle_task_self(
    db: AsyncIOMotorDatabase, task_id: str, nurse_id: str
) -> TaskResponse:
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if str(task.get("assigned_to")) != nurse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the original assignee can handle the task themselves",
        )

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

    updated_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    updated_task = await enrich_task_with_names(db, updated_task)
    updated_task = await enrich_task_with_room(db, updated_task)

    return TaskResponse(**updated_task)


async def update_task_status(db: AsyncIOMotorDatabase, task: dict) -> dict:
    now = datetime.now(timezone.utc)
    task_id = task["_id"]
    current_status = task.get("status")

    if current_status == TaskStatus.COMPLETED:
        return task

    if current_status in [
        TaskStatus.REASSIGNMENT_REQUESTED,
        TaskStatus.REASSIGNMENT_REJECTED,
    ]:
        return task

    status_update = None

    if (
        "due_date" in task
        and task["due_date"] < now
        and current_status != TaskStatus.DELAYED
    ):
        status_update = TaskStatus.DELAYED

    elif (
        "due_date" in task
        and task["due_date"] >= now
        and current_status != TaskStatus.ASSIGNED
    ):
        status_update = TaskStatus.ASSIGNED

    if status_update:
        await db.tasks.update_one({"_id": task_id}, {"$set": {"status": status_update}})
        task["status"] = status_update

    return task


async def download_tasks(db: AsyncIOMotorDatabase, task_ids: List[str]) -> bytes:
    """Download multiple tasks in a single PDF."""
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )
    styles = getSampleStyleSheet()

    # Create custom styles for the content
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"], fontSize=16, spaceAfter=30
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle", parent=styles["Heading2"], fontSize=14, spaceAfter=20
    )

    cell_style = ParagraphStyle(
        "CellStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,  # Line height
        wordWrap="CJK",  # Enable word wrapping
        splitLongWords=True,
    )

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.white,
        wordWrap="CJK",
    )

    story = []

    # Title
    story.append(Paragraph("Tasks Report", title_style))
    story.append(Spacer(1, 12))

    for task_id in task_ids:
        try:
            task = await get_task_by_id(db, task_id)
            task_dict = task.model_dump()

            # Enrich task with names and room information
            task_dict = await enrich_task_with_names(db, task_dict)
            task_dict = await enrich_task_with_room(db, task_dict)

            # Task Title
            story.append(Paragraph(f"Task: {task_dict['task_title']}", subtitle_style))
            story.append(Spacer(1, 12))

            # Convert data to paragraphs for proper wrapping
            data = [
                [
                    Paragraph("Status:", header_style),
                    Paragraph(task_dict["status"], cell_style),
                ],
                [
                    Paragraph("Priority:", header_style),
                    Paragraph(task_dict["priority"], cell_style),
                ],
                [
                    Paragraph("Category:", header_style),
                    Paragraph(task_dict["category"], cell_style),
                ],
                [
                    Paragraph("Details:", header_style),
                    Paragraph(task_dict["task_details"], cell_style),
                ],
                [
                    Paragraph("Resident:", header_style),
                    Paragraph(task_dict.get("resident_name", "N/A"), cell_style),
                ],
                [
                    Paragraph("Room:", header_style),
                    Paragraph(task_dict.get("resident_room", "N/A"), cell_style),
                ],
                [
                    Paragraph("Assigned To:", header_style),
                    Paragraph(task_dict.get("assigned_to_name", "N/A"), cell_style),
                ],
                [
                    Paragraph("Start Date:", header_style),
                    Paragraph(
                        task_dict["start_date"].strftime("%Y-%m-%d %H:%M"), cell_style
                    ),
                ],
                [
                    Paragraph("Due Date:", header_style),
                    Paragraph(
                        (
                            task_dict["due_date"].strftime("%Y-%m-%d %H:%M")
                            if task_dict.get("due_date")
                            else "N/A"
                        ),
                        cell_style,
                    ),
                ],
                [
                    Paragraph("Created At:", header_style),
                    Paragraph(
                        task_dict["created_at"].strftime("%Y-%m-%d %H:%M"), cell_style
                    ),
                ],
                [
                    Paragraph("Last Updated:", header_style),
                    Paragraph(str(task_dict.get("updated_at", "N/A")), cell_style),
                ],
                [
                    Paragraph("Recurring:", header_style),
                    Paragraph(str(task_dict.get("recurring", "No")), cell_style),
                ],
                [
                    Paragraph("Series ID:", header_style),
                    Paragraph(str(task_dict.get("series_id", "N/A")), cell_style),
                ],
            ]

            # Create table with auto-width columns
            table = Table(data, colWidths=[2 * inch, 4 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.blue),
                        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                        ("TOPPADDING", (0, 0), (-1, -1), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),  # Align text to top of cells
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),  # Add left padding
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),  # Add right padding
                    ]
                )
            )

            story.append(table)
            story.append(PageBreak())

        except Exception as e:
            print(f"Error processing task {task_id}: {e}")
            continue

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
