from pydantic import BaseModel
from datetime import date


class FixedMedication(BaseModel):
    medication_id: str  # Unique barcode ID
    medication_name: str
    dosage: str
    frequency: str
    expiry_date: date
    instructions: str
