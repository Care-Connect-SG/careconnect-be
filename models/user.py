from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from db.base import PyObjectId, BaseConfig

class Role(str, Enum):
    ADMIN = "Admin"
    NURSE = "Nurse"
    FAMILY = "Family"

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"

class UserBase(BaseModel):
    email: EmailStr
    name: str
    password: str
    contact_number: Optional[str] = None
    role: Role
    organisation_rank: Optional[str] = None
    gender: Gender

    class Config(BaseConfig):
        populate_by_name = True

class User(UserBase):
     id: Optional[PyObjectId] = Field(alias="_id", default=None)

class Token(BaseModel):
    access_token: str
    token_type: str
    email: str
