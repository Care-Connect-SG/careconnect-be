from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from models.base import ModelConfig, PyObjectId


class MedicationCreate(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None


class MedicationResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    resident_id: Optional[PyObjectId] = None
    medication_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None
