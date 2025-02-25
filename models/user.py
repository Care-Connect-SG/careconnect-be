from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from db.base import PyObjectId, BaseConfig
from auth.hashing import Hash

class Role(Enum):
    ADMIN = "ADMIN"
    NURSE = "NURSE"
    FAMILY = "FAMILY" 

class Gender(Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class User(BaseModel):
    id: PyObjectId = Field(..., alias="_id")  # This is now compulsory, so '...' means it must be provided
    email: EmailStr
    name: str
    password: str
    contact_number: Optional[str] = None
    role: Role
    organisation_rank: Optional[str] = None
    gender: Gender

    # Hash password before saving
    @field_validator('password')
    def hash_password(cls, value):
        return Hash.bcrypt(value)
    
    class Config(BaseConfig):
        pass

class Token(BaseModel):
    access_token: str
    token_type: str
    email: str