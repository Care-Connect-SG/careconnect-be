from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from models.base import ModelConfig, PyObjectId


class TaskStatus(str, Enum):
    ASSIGNED = "Assigned"
    COMPLETED = "Completed"
    DELAYED = "Delayed"
    REQUEST_REASSIGNMENT = "Request Reassignment"


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
    status: TaskStatus = TaskStatus.ASSIGNED
    priority: Optional[TaskPriority] = None
    category: Optional[TaskCategory] = None
    assigned_to: PyObjectId
    residents: List[PyObjectId]
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    start_date: datetime
    due_date: datetime
    recurring: Optional[Recurrence] = None
    end_recurring_date: Optional[datetime] = None
    remind_prior: Optional[int] = None
    finished_at: Optional[datetime] = None
    media: Optional[List[str]] = None
    notes: Optional[str] = None
    is_ai_generated: bool = False


class TaskResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    task_title: str = Field(..., min_length=3, max_length=255)
    task_details: Optional[str] = None
    status: TaskStatus = TaskStatus.ASSIGNED
    priority: Optional[TaskPriority] = None
    category: Optional[TaskCategory] = None
    assigned_to: PyObjectId
    residents: List[PyObjectId]
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    start_date: datetime
    due_date: datetime
    recurring: Optional[Recurrence] = None
    end_recurring_date: Optional[datetime] = None
    remind_prior: Optional[int] = None
    finished_at: Optional[datetime] = None
    media: Optional[List[str]] = None
    notes: Optional[str] = None
    is_ai_generated: bool = False
