from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from models.base import ModelConfig, PyObjectId
from models.resident import ResidentTagResponse
from models.user import UserTagResponse


class ReportStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"


class ReportSectionContent(BaseModel):
    form_element_id: str
    input: str | List[str]


class ReportCreate(BaseModel):
    form_id: Optional[PyObjectId] = Field(alias="_id", default=None)
    form_name: str
    reporter: UserTagResponse
    primary_resident: Optional[ResidentTagResponse] = None
    involved_residents: List[ResidentTagResponse] = Field(default_factory=list)
    involved_caregivers: List[UserTagResponse] = Field(default_factory=list) 
    report_content: List[ReportSectionContent]
    status: ReportStatus


class ReportResponse(ReportCreate, ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
