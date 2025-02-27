from pydantic import BaseModel
from typing import List, Optional

class Group(BaseModel):
    name: str
    description: str
    members: Optional[List[str]] = []  # Default to an empty list

class GroupCreate(BaseModel):
    group_id: Optional[str]  # Group id is optional
    name: str
    description: str