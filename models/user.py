from pydantic import BaseModel

class User(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    email: str

