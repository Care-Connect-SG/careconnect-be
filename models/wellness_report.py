from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class WellnessReportCreate(BaseModel):
    date: date  # Date of the report
    monthly_summary: Optional[str] = None
    medical_summary: Optional[str] = None
    medication_update: Optional[str] = None
    nutrition_hydration: Optional[str] = None
    mobility_physical: Optional[str] = None
    cognitive_emotional: Optional[str] = None
    social_engagement: Optional[str] = None


class WellnessReportResponse(WellnessReportCreate):
    id: str
    resident_id: str
