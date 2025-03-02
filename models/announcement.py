from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from models.base import ModelConfig, PyObjectId


class AnnouncementCreate(BaseModel):
    title: str
    message: str
    group_names: List[str]  # Changed from group_ids to group_names
    scheduled_time: Optional[datetime] = None


class AnnouncementResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str
    message: str
    group_names: List[str]  # Changed from group_ids to group_names
    created_at: datetime
    scheduled_time: Optional[datetime] = None
