from pydantic import BaseModel
from typing import List, Optional

class ReportSectionContent(BaseModel):
    form_element_id: str
    input: str | List[str]

class ReportCreate(BaseModel):
    form_id: str
    reporter_id: str
    primary_resident: Optional[str] = None
    involved_residents: Optional[List[str]] = []
    involved_caregivers: Optional[List[str]] = []
    report_content: List[ReportSectionContent]
    status: str

class ReportResponse(ReportCreate):
    _id: str
    created_date: str
    published_date: Optional[str] = None
    
