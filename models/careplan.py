from pydantic import BaseModel
from datetime import date
from typing import Optional


class CarePlanCreate(BaseModel):
    resident_id: str
    created_date: date
    medical_conditions: Optional[str] = None
    doctor_appointments: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    daily_meal_plan: Optional[str] = None
    hydration: Optional[str] = None
    nutritional_supplements: Optional[str] = None
    bathing_assistance: Optional[bool] = None
    dressing_assistance: Optional[bool] = None
    required_assistance: Optional[str] = None
    hobbies_interests: Optional[str] = None
    social_interaction_plan: Optional[str] = None


class CarePlanResponse(BaseModel):
    id: str
    resident_id: str
    created_date: date
    last_updated: Optional[date] = None
    medical_conditions: Optional[str] = None
    doctor_appointments: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    daily_meal_plan: Optional[str] = None
    hydration: Optional[str] = None
    nutritional_supplements: Optional[str] = None
    bathing_assistance: Optional[bool] = None
    dressing_assistance: Optional[bool] = None
    required_assistance: Optional[str] = None
    hobbies_interests: Optional[str] = None
    social_interaction_plan: Optional[str] = None
