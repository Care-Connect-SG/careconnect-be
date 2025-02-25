from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class FormBase(BaseModel):
    title: str
    description: Optional[str] = ""
    creator_id: str
    json_content: Dict

class FormComplete(FormBase):
    _id: str
    created_date: datetime
    status: str