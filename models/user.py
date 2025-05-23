from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from models.base import ModelConfig, PyObjectId


class Role(str, Enum):
    ADMIN = "Admin"
    NURSE = "Nurse"


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
    profile_picture: Optional[str] = None
    telegram_handle: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserUpdate(BaseModel):
    name: Optional[str] = None
    contact_number: Optional[str] = None
    organisation_rank: Optional[str] = None
    profile_picture: Optional[str] = None
    gender: Optional[Gender] = None
    telegram_handle: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    current_password: str = Field(..., description="The user's current password")
    new_password: str = Field(..., description="The new password")


class UserResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr
    name: str
    contact_number: Optional[str] = None
    role: Role
    organisation_rank: Optional[str] = None
    profile_picture: Optional[str] = None
    gender: Gender
    telegram_handle: Optional[str] = None


class UserTagResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    role: str


class Token(BaseModel):
    id: str
    name: str
    email: str
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
