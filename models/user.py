from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    email: str


class TokenData(BaseModel):
    email: Optional[str] = None
