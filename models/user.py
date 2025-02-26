from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from db.base import PyObjectId, BaseConfig

class Role(str, Enum):
    ADMIN = "ADMIN"
    NURSE = "NURSE"
    FAMILY = "FAMILY" 

class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    password: str
    contact_number: Optional[str] = None
    role: Role
    organisation_rank: Optional[str] = None
    gender: Gender
    
    class Config(BaseConfig):
        pass

class Token(BaseModel):
    access_token: str
    token_type: str
    email: str