from pydantic import BaseModel
from datetime import date
from typing import Optional


class MedicationCreate(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None


class MedicationResponse(BaseModel):
    id: str
    resident_id: str
    medication_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None
