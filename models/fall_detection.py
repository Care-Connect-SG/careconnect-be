from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

from models.base import ModelConfig, PyObjectId


class FallLogCreate(BaseModel):
    resident_id: str = "67bd9832c775476225864ac7"  # Mock as Jane for now
    device_id: str = "mock_wearable_12345"  # Mock wearable device for now
    acceleration_magnitude: float
    status: Literal["pending", "confirmed", "false_positive"] = "pending"
    incident_report_id: Optional[str] = None


class FallLogResponse(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    resident_id: str
    device_id: str
    timestamp: datetime
    acceleration_magnitude: float
    status: Literal["pending", "confirmed", "false_positive"]
    incident_report_id: Optional[str] = None
