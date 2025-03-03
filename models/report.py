from pydantic import BaseModel
from typing import List

class ReportSectionContent(BaseModel):
    form_element_id: str
    input: str | List[str]

class ReportBase(BaseModel):
    form_id: str
    reporter_id: str
    report_content: List[ReportSectionContent]
    status: str

class ReportComplete(ReportBase):
    _id: str
    created_date: str
    
