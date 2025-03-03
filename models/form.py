from pydantic import BaseModel
from typing import List

class FormElement(BaseModel):
    element_id: str
    type: str
    label: str
    helptext: str
    required: bool
    options: List[str] = []

class FormCreate(BaseModel):
    title: str
    description: str
    creator_id: str
    json_content: List[FormElement]
    status: str

class FormResponse(FormCreate):
    _id: str
    created_date: str
