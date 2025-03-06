from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from models.base import PyObjectId
from models.resident import ResidentTagResponse
from models.user import CaregiverTagResponse


class ReportStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"


class ReportSectionContent(BaseModel):
    form_element_id: str
    input: str | List[str]


class ReportCreate(BaseModel):
    form_id: str
    form_name: str
    reporter: CaregiverTagResponse
    primary_resident: Optional[ResidentTagResponse] = None
    involved_residents: Optional[List[ResidentTagResponse]] = []
    involved_caregivers: Optional[List[CaregiverTagResponse]] = []
    report_content: List[ReportSectionContent]
    status: str


class ReportResponse(ReportCreate):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_date: str
    published_date: Optional[str] = None
    
