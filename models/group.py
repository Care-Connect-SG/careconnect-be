from pydantic import BaseModel
from typing import List, Optional


class GroupCreate(BaseModel):
    name: str
    description: str


class GroupResponse(BaseModel):
    name: str
    description: str
    members: Optional[List[str]] = []
