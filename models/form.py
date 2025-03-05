from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Optional

from models.base import PyObjectId


class FormElement(BaseModel):
    element_id: str
    type: str
    label: str
    helptext: str
    required: bool
    options: List[str] = []


class FormCreate(BaseModel):
    title: str
    description: str
    creator_id: str
    json_content: List[FormElement]
    status: str


class FormResponse(FormCreate):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
