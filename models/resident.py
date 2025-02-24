from pydantic import BaseModel
from datetime import date
from typing import Optional

class RegistrationCreate(BaseModel):
    full_name: str
    gender: str
    date_of_birth: date
    nric_number: str
    emergency_contact_name: str
    emergency_contact_number: str
    relationship: str
    room_number: Optional[str] = None  # Allow auto-assignment if omitted
    additional_notes: Optional[str] = None
