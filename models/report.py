from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from models.base import ModelConfig, PyObjectId
from models.resident import ResidentTagResponse
from models.user import UserTagResponse


class ReportStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    SUBMITTED = "Submitted"
    CHANGES_REQUESTED = "Changes Requested"
    CHANGES_MADE = "Changes Made"


class ReportSectionContent(BaseModel):
    form_element_id: str
    input: str | List[str]


class ReportReviewStatus(str, Enum):
    PENDING = "Pending"
    RESOLVED = "Resolved"


class ReportReviewCreate(BaseModel):
    review_id: str
    reviewer: UserTagResponse
    review: str


class ReportReview(ReportReviewCreate):
    resolution: Optional[str] = None
    status: ReportReviewStatus
    reviewed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class ResolveReportRequest(BaseModel):
    resolution: str


class ReportCreate(BaseModel):
    form_id: Optional[PyObjectId] = None
    form_name: str
    reporter: UserTagResponse
    primary_resident: Optional[ResidentTagResponse] = None
    involved_residents: List[ResidentTagResponse] = Field(default_factory=list)
    involved_caregivers: List[UserTagResponse] = Field(default_factory=list)
    report_content: List[ReportSectionContent]
    status: ReportStatus
    reference_report_id: Optional[PyObjectId] = None
    reviews: List[ReportReview] = Field(default_factory=list)


class ReportResponse(ReportCreate, ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submittted_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
