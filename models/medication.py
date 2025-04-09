from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from models.base import ModelConfig, PyObjectId


class ScheduleType(str, Enum):
    DAY = "day"
    WEEK = "week"
    CUSTOM = "custom"


class TimeOfDay(BaseModel):
    hour: int
    minute: int


class MedicationCreate(BaseModel):
    medication_name: str
    dosage: str
    start_date: date
    end_date: Optional[date] = None
    schedule_type: ScheduleType
    repeat: Optional[int] = None
    times_of_day: List[TimeOfDay] = Field(default_factory=list)
    days_of_week: List[str] = Field(default_factory=list)
    instructions: Optional[str] = None


class MedicationResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    resident_id: Optional[PyObjectId] = None
    medication_name: str
    dosage: str
    start_date: date
    end_date: Optional[date] = None
    schedule_type: ScheduleType
    repeat: Optional[int] = None
    times_of_day: List[TimeOfDay] = Field(default_factory=list)
    days_of_week: List[str] = Field(default_factory=list)
    instructions: Optional[str] = None
