from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field

from models.base import ModelConfig, PyObjectId


class WellnessReportCreate(BaseModel):
    date: date
    monthly_summary: Optional[str] = None
    medical_summary: Optional[str] = None
    medication_update: Optional[str] = None
    nutrition_hydration: Optional[str] = None
    mobility_physical: Optional[str] = None
    cognitive_emotional: Optional[str] = None
    social_engagement: Optional[str] = None
    is_ai_generated: Optional[bool] = False
    ai_confidence_score: Optional[float] = None
    ai_recommendations: Optional[List[str]] = None


class WellnessReportResponse(WellnessReportCreate, ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    resident_id: Optional[PyObjectId] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
