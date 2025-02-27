from pydantic import BaseModel
from typing import List, Optional

class Group(BaseModel):
    name: str
    description: str
    members: Optional[List[str]] = []  # Default to an empty list

class GroupCreate(BaseModel):
    name: str
    description: str