from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from db.base import PyObjectId, BaseConfig

class EventType(str, Enum):
    TASK = "Task"
    EVENT = "Event"

class Recurrence(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    ANNUALLY = "Annually"

class CalendarEvent(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    event_type: EventType
    related_task_id: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    recurring: Optional[Recurrence] = None
    end_recurring_date: Optional[date] = None
    participants: List[str] = []
    remind_prior: Optional[int] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config(BaseConfig):
        pass
