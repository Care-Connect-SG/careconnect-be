from typing import List, Optional

from pydantic import BaseModel, Field

from models.base import ModelConfig, PyObjectId


class GroupCreate(BaseModel):
    name: str
    description: str
    members: Optional[List[PyObjectId]] = []


class GroupResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    description: str
    members: Optional[List[PyObjectId]] = []
