from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from db.base import PyObjectId, BaseConfig

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

# Base model containing fields common to both input and output
class TaskBase(BaseModel):
    task_title: str = Field(..., min_length=3, max_length=255)
    task_details: Optional[str] = None
    status: TaskStatus = TaskStatus.ASSIGNED
    priority: Optional[TaskPriority] = None
    category: Optional[TaskCategory] = None
    assigned_to: List[str] = []
    resident: str
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    recurring: Optional[Recurrence] = None
    end_recurring_date: Optional[date] = None
    remind_prior: Optional[int] = None
    finished_at: Optional[datetime] = None
    media: Optional[List[str]] = None
    notes: Optional[str] = None
    is_ai_generated: bool = False
    calendar_event_id: Optional[str] = None

    class Config(BaseConfig):
        # Use Pydantic V2 key for population by field name
        populate_by_name = True

# Input model for creating/updating tasks (excludes id)
class TaskCreate(TaskBase):
    pass

# Output model for tasks (includes id with alias)
class Task(TaskBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
