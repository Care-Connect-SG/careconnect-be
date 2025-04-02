from typing import List

from fastapi import APIRouter

from models.fixed_medication import FixedMedication
from services.fixed_medication_service import get_all_medications, get_medication_by_id

router = APIRouter(prefix="/fixedmedications", tags=["Fixed Medications"])


@router.get("/", response_model=List[FixedMedication], response_model_by_alias=False)
async def list_medications():
    return get_all_medications()


@router.get(
    "/{medication_id}", response_model=FixedMedication, response_model_by_alias=False
)
async def get_medication(medication_id: str):
    return await get_medication_by_id(medication_id)
