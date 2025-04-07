from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from models.base import ModelConfig, PyObjectId


class ActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    visibility: bool = True
    reminder_minutes: Optional[int] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(ActivityBase):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reminder_minutes: Optional[int] = None


class ActivityResponse(ActivityBase, ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_by: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
