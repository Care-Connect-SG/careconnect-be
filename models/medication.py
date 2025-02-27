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
    id: str  # Unique medication record ID
    resident_id: str  # The resident this medication belongs to
    medication_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None
    
