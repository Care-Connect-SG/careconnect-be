from enum import Enum
from pydantic import BaseModel, EmailStr
from typing import Optional
from db.base import BaseConfig

class Role(str, Enum):
    ADMIN = "ADMIN"
    NURSE = "NURSE"
    FAMILY = "Family"

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
