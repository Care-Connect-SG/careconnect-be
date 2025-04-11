from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from models.base import ModelConfig, PyObjectId


class RegistrationCreate(BaseModel):
    photograph: Optional[str] = None
    full_name: str
    gender: str
    date_of_birth: date
    nric_number: str
    emergency_contact_name: str
    emergency_contact_number: str
    relationship: str
    room_number: Optional[str] = None
    additional_notes: Optional[List[str]] = None
    additional_notes_timestamp: Optional[List[datetime]] = None
    primary_nurse: Optional[str] = None


class RegistrationResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    photograph: Optional[str] = None
    full_name: str
    gender: str
    date_of_birth: date
    nric_number: str
    emergency_contact_name: str
    emergency_contact_number: str
    relationship: str
    room_number: str
    admission_date: date
    additional_notes: Optional[List[str]] = None
    additional_notes_timestamp: Optional[List[datetime]] = None
    primary_nurse: Optional[str] = None


class RegistrationUpdate(ModelConfig):
    photograph: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    nric_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    relationship: Optional[str] = None
    room_number: Optional[str] = None
    additional_notes: Optional[List[str]] = None
    additional_notes_timestamp: Optional[List[datetime]] = None
    primary_nurse: Optional[str] = None


class ResidentTagResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
