from datetime import date
from typing import Optional

from pydantic import Field

from models.base import ModelConfig, PyObjectId


class FixedMedication(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    medication_name: str
    dosage: str
    frequency: str
    expiry_date: date
    instructions: str
