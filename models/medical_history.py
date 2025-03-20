from pydantic import Field
from typing import Optional
from datetime import date
from models.base import ModelConfig, PyObjectId


class ConditionRecord(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    condition_name: str
    date_of_diagnosis: date
    treating_physician: str
    treatment_details: str
    current_status: str
    resident_id: Optional[str] = None


class AllergyRecord(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    allergen: str
    reaction_description: str
    date_first_noted: date
    severity: str
    management_notes: Optional[str] = None
    resident_id: Optional[str] = None


class ChronicIllnessRecord(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    illness_name: str
    date_of_onset: date
    managing_physician: str
    current_treatment_plan: str
    monitoring_parameters: str
    resident_id: Optional[str] = None


class SurgicalHistoryRecord(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    procedure: str
    date: date
    surgeon: str
    hospital: str
    complications: Optional[str] = None
    resident_id: Optional[str] = None


class ImmunizationRecord(ModelConfig):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    vaccine: str
    date_administered: date
    administering_facility: str
    next_due_date: Optional[date] = None
    resident_id: Optional[str] = None
