from pydantic import Field, BaseModel
from typing import Optional, Union
from datetime import date
from models.base import ModelConfig, PyObjectId
from enum import Enum


class MedicalRecordType(str, Enum):
    CONDITION = "condition"
    ALLERGY = "allergy"
    CHRONIC_ILLNESS = "chronic"
    SURGICAL = "surgical"
    IMMUNIZATION = "immunization"


class BaseMedicalRecord(ModelConfig):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    resident_id: Optional[PyObjectId] = None
    created_at: date = Field(default_factory=date.today)
    updated_at: date = Field(default_factory=date.today)


class ConditionRecord(BaseMedicalRecord):
    condition_name: str
    date_of_diagnosis: date
    treating_physician: str
    treatment_details: str
    current_status: str


class AllergyRecord(BaseMedicalRecord):
    allergen: str
    reaction_description: str
    date_first_noted: date
    severity: str
    management_notes: Optional[str] = None


class ChronicIllnessRecord(BaseMedicalRecord):
    illness_name: str
    date_of_onset: date
    managing_physician: str
    current_treatment_plan: str
    monitoring_parameters: str


class SurgicalHistoryRecord(BaseMedicalRecord):
    procedure: str
    surgery_date: date
    surgeon: str
    hospital: str
    complications: Optional[str] = None


class ImmunizationRecord(BaseMedicalRecord):
    vaccine: str
    date_administered: date
    administering_facility: str
    next_due_date: Optional[date] = None


class CreateMedicalRecordRequest(BaseModel):
    record_type: MedicalRecordType
    resident_id: Optional[PyObjectId] = None
    record_data: dict


MedicalRecordUnion = Union[
    ConditionRecord,
    AllergyRecord,
    ChronicIllnessRecord,
    SurgicalHistoryRecord,
    ImmunizationRecord,
]
