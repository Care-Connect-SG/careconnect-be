from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from db.base import PyObjectId

class MedicationCreate(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None

class MedicationResponse(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    resident_id: str
    medication_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None

