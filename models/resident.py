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
    room_number: Optional[str] = None 
    additional_notes: Optional[str] = None
    primary_nurse: Optional[str] = None


class RegistrationResponse(BaseModel):
    id: str
    full_name: str
    gender: str
    date_of_birth: date 
    nric_number: str
    emergency_contact_name: str
    emergency_contact_number: str
    relationship: str
    room_number: str
    admission_date: date
    additional_notes: Optional[str] = None
    primary_nurse: Optional[str] = None