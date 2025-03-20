from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from models.base import ModelConfig, PyObjectId

class ActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    visibility: bool = True

    model_config = {
        'json_schema_extra': {
            'example': {
                'title': 'Morning Exercise',
                'description': 'Daily morning exercise session',
                'start_time': '2024-03-15T09:00:00',
                'end_time': '2024-03-15T10:00:00',
                'location': 'Nursing Home Yard',
                'category': 'Workshop',
                'tags': 'exercise,morning,health',
                'visibility': True
            }
        }
    }

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(ActivityBase):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class Activity(ActivityBase, ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ActivityFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    search: Optional[str] = None 