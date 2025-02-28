from pydantic import BaseModel
from typing import List, Optional


class GroupCreate(BaseModel):
    group_id: Optional[str]  # Group id is optional
    name: str
    description: str


class GroupResponse(BaseModel):
    name: str
    description: str
    members: Optional[List[str]] = []
