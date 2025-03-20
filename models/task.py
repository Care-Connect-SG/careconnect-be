from pydantic import BaseModel, Field
from datetime import datetime, timezone, date
from typing import Optional, List
from enum import Enum
from models.base import ModelConfig, PyObjectId


class TaskStatus(str, Enum):
    ASSIGNED = "Assigned"
    COMPLETED = "Completed"
    DELAYED = "Delayed"
    REASSIGNMENT_REQUESTED = "Reassignment Requested"
    REASSIGNMENT_REJECTED = "Reassignment Rejected"


class TaskPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TaskCategory(str, Enum):
    MEALS = "Meals"
    MEDICATION = "Medication"
    THERAPY = "Therapy"
    OUTING = "Outing"


class Recurrence(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    ANNUALLY = "Annually"


class TaskCreate(BaseModel):
    task_title: str = Field(..., min_length=3, max_length=255)
    task_details: Optional[str] = None
    media: Optional[List[str]] = None
    notes: Optional[str] = None
    status: TaskStatus = TaskStatus.ASSIGNED
    priority: Optional[TaskPriority] = None
    category: Optional[TaskCategory] = None
    residents: List[PyObjectId]
    start_date: datetime
    due_date: datetime
    recurring: Optional[Recurrence] = None
    end_recurring_date: Optional[date] = None
    remind_prior: Optional[int] = None
    is_ai_generated: bool = False
    assigned_to: PyObjectId
    reassignment_requested_to: Optional[PyObjectId] = None
    reassignment_requested_by: Optional[PyObjectId] = None
    reassignment_requested_at: Optional[datetime] = None
    reassignment_rejection_reason: Optional[str] = None
    reassignment_rejected_at: Optional[datetime] = None
    series_id: Optional[str] = None


class TaskUpdate(BaseModel):
    task_title: Optional[str] = Field(None, min_length=3, max_length=255)
    task_details: Optional[str] = None
    media: Optional[List[str]] = None
    notes: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    category: Optional[TaskCategory] = None
    residents: Optional[List[PyObjectId]] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    recurring: Optional[Recurrence] = None
    end_recurring_date: Optional[date] = None
    remind_prior: Optional[int] = None
    is_ai_generated: Optional[bool] = None
    assigned_to: Optional[PyObjectId] = None
    reassignment_requested_to: Optional[PyObjectId] = None
    reassignment_requested_by: Optional[PyObjectId] = None
    reassignment_requested_at: Optional[datetime] = None
    reassignment_rejection_reason: Optional[str] = None
    reassignment_rejected_at: Optional[datetime] = None
    update_series: Optional[bool] = False


class TaskResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    task_title: str = Field(..., min_length=3, max_length=255)
    task_details: Optional[str] = None
    media: Optional[List[str]] = None
    notes: Optional[str] = None
    status: TaskStatus = TaskStatus.ASSIGNED
    priority: Optional[TaskPriority] = None
    category: Optional[TaskCategory] = None
    start_date: datetime
    due_date: datetime
    recurring: Optional[Recurrence] = None
    end_recurring_date: Optional[date] = None
    remind_prior: Optional[int] = None
    finished_at: Optional[datetime] = None
    is_ai_generated: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assigned_to: PyObjectId
    assigned_to_name: str = "Unknown"
    resident: PyObjectId
    resident_name: str = "Unknown"
    resident_room: str = "Unknown"
    created_by: PyObjectId
    reassignment_requested_to: Optional[PyObjectId] = None
    reassignment_requested_to_name: Optional[str] = "Unknown"
    reassignment_requested_by: Optional[PyObjectId] = None
    reassignment_requested_by_name: Optional[str] = "Unknown"
    reassignment_requested_at: Optional[datetime] = None
    reassignment_rejection_reason: Optional[str] = None
    reassignment_rejected_at: Optional[datetime] = None
    series_id: Optional[str] = None
