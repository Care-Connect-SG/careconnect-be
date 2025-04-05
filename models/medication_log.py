from datetime import datetime
from typing import Optional

from pydantic import Field

from models.base import ModelConfig, PyObjectId


class MedicationAdministrationLog(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    resident_id: PyObjectId
    medication_id: PyObjectId
    nurse: Optional[str] = None
    administered_at: datetime
