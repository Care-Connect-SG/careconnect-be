from pydantic import Field, BaseModel
from typing import Optional, Literal
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
    """Base class for all medical records with common fields"""
    record_id: Optional[PyObjectId] = Field(default=None, alias="_id", description="MongoDB ObjectId")
    resident_id: str = Field(..., description="ID of the resident this record belongs to")
    created_at: date = Field(default_factory=date.today, description="Date the record was created")
    updated_at: date = Field(default_factory=date.today, description="Date the record was last updated")


class ConditionRecord(BaseMedicalRecord):
    """Medical condition record"""
    condition_name: str = Field(..., description="Name of the medical condition")
    date_of_diagnosis: date = Field(..., description="Date when the condition was diagnosed")
    treating_physician: str = Field(..., description="Name of the treating physician")
    treatment_details: str = Field(..., description="Details of the treatment plan")
    current_status: str = Field(..., description="Current status of the condition")


class AllergyRecord(BaseMedicalRecord):
    """Allergy record"""
    allergen: str = Field(..., description="Name of the allergen")
    reaction_description: str = Field(..., description="Description of the allergic reaction")
    date_first_noted: date = Field(..., description="Date when the allergy was first noted")
    severity: str = Field(..., description="Severity of the allergic reaction")
    management_notes: Optional[str] = Field(None, description="Notes on managing the allergy")


class ChronicIllnessRecord(BaseMedicalRecord):
    """Chronic illness record"""
    illness_name: str = Field(..., description="Name of the chronic illness")
    date_of_onset: date = Field(..., description="Date when the illness started")
    managing_physician: str = Field(..., description="Name of the managing physician")
    current_treatment_plan: str = Field(..., description="Current treatment plan details")
    monitoring_parameters: str = Field(..., description="Parameters being monitored")


class SurgicalHistoryRecord(BaseMedicalRecord):
    """Surgical history record"""
    procedure: str = Field(..., description="Name of the surgical procedure")
    surgery_date: date = Field(..., description="Date of the surgery")
    surgeon: str = Field(..., description="Name of the surgeon")
    hospital: str = Field(..., description="Hospital where the surgery was performed")
    complications: Optional[str] = Field(None, description="Any complications during or after surgery")


class ImmunizationRecord(BaseMedicalRecord):
    """Immunization record"""
    vaccine: str = Field(..., description="Name of the vaccine")
    date_administered: date = Field(..., description="Date when the vaccine was administered")
    administering_facility: str = Field(..., description="Facility where the vaccine was administered")
    next_due_date: Optional[date] = Field(None, description="Date when the next dose is due")


class CreateMedicalRecordRequest(BaseModel):
    """Request model for creating a medical record"""
    record_type: MedicalRecordType = Field(..., description="Type of medical record")
    resident_id: str = Field(..., description="ID of the resident")
    record_data: dict = Field(..., description="Record data specific to the record type")
