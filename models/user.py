from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from models.base import ModelConfig, PyObjectId


class Role(str, Enum):
    ADMIN = "Admin"
    NURSE = "Nurse"
    FAMILY = "Family"


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    contact_number: Optional[str] = None
    role: Role
    organisation_rank: Optional[str] = None
    gender: Gender


class UserResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr
    name: str
    password: str
    contact_number: Optional[str] = None
    role: Role
    organisation_rank: Optional[str] = None
    gender: Gender


class Token(BaseModel):
    access_token: str
    token_type: str
    email: str
