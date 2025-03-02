from pydantic import BaseModel, Field
from typing import List, Optional
from models.base import ModelConfig, PyObjectId


class GroupCreate(BaseModel):
    
    name: str
    description: str


class GroupResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    description: str
    members: Optional[List[str]] = []
