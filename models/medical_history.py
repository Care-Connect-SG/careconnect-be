from pydantic import Field, BaseModel
from typing import Optional, Union
from datetime import date
from models.base import ModelConfig, PyObjectId
from enum import Enum


class MedicalHistoryType(str, Enum):
    CONDITION = "condition"
    ALLERGY = "allergy"
    CHRONIC_ILLNESS = "chronic"
    SURGICAL = "surgical"
    IMMUNIZATION = "immunization"


class BaseMedicalHistory(ModelConfig):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    resident_id: Optional[PyObjectId] = None
    created_at: date = Field(default_factory=date.today)
    updated_at: date = Field(default_factory=date.today)


class ConditionRecord(BaseMedicalHistory):
    condition_name: str
    date_of_diagnosis: date
    treating_physician: str
    treatment_details: str
    current_status: str


class AllergyRecord(BaseMedicalHistory):
    allergen: str
    reaction_description: str
    date_first_noted: date
    severity: str
    management_notes: Optional[str] = None


class ChronicIllnessRecord(BaseMedicalHistory):
    illness_name: str
    date_of_onset: date
    managing_physician: str
    current_treatment_plan: str
    monitoring_parameters: str


class SurgicalHistoryRecord(BaseMedicalHistory):
    procedure: str
    surgery_date: date
    surgeon: str
    hospital: str
    complications: Optional[str] = None


class ImmunizationRecord(BaseMedicalHistory):
    vaccine: str
    date_administered: date
    administering_facility: str
    next_due_date: Optional[date] = None


class MedicalHistoryCreate(BaseModel):
    record_type: MedicalHistoryType
    resident_id: Optional[PyObjectId] = None
    record_data: dict


MedicalHistoryUnion = Union[
    ConditionRecord,
    AllergyRecord,
    ChronicIllnessRecord,
    SurgicalHistoryRecord,
    ImmunizationRecord,
]
