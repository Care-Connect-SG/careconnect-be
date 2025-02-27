from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from db.base import PyObjectId

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
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
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

