import datetime
from typing import List, Optional

from fastapi import HTTPException

from models.fixed_medication import FixedMedication

FIXED_MEDICATIONS_DATA = [
    FixedMedication(
        id="1234567",
        medication_name="Aspirin",
        dosage="100mg",
        frequency="Twice a day",
        expiry_date=datetime.date(2025, 12, 31),
        instructions="Take with food",
    ),
    FixedMedication(
        id="2345678",
        medication_name="Ibuprofen",
        dosage="200mg",
        frequency="Once a day",
        expiry_date=datetime.date(2025, 11, 15),
        instructions="Take after meals",
    ),
    FixedMedication(
        id="3456789",
        medication_name="Paracetamol",
        dosage="500mg",
        frequency="Every 6 hours as needed",
        expiry_date=datetime.date(2026, 1, 20),
        instructions="Do not exceed 4g per day",
    ),
    FixedMedication(
        id="3893809",
        medication_name="Paracetamol",
        dosage="500mg",
        frequency="Every 6 hours as needed",
        expiry_date=datetime.date(2026, 1, 20),
        instructions="Do not exceed 4g per day",
    ),
    FixedMedication(
        id="5678901",
        medication_name="Amoxicillin",
        dosage="500mg",
        frequency="Every 8 hours",
        expiry_date=datetime.date(2025, 9, 30),
        instructions="Complete full course even if symptoms improve",
    ),
    FixedMedication(
        id="6789012",
        medication_name="Atorvastatin",
        dosage="10mg",
        frequency="Once daily at bedtime",
        expiry_date=datetime.date(2027, 3, 10),
        instructions="Avoid grapefruit juice while taking this medication",
    ),
    FixedMedication(
        id="7890123",
        medication_name="Metformin",
        dosage="500mg",
        frequency="Twice daily with meals",
        expiry_date=datetime.date(2026, 6, 25),
        instructions="Monitor blood sugar levels regularly",
    ),
]


async def get_all_medications() -> List[FixedMedication]:
    try:
        return FIXED_MEDICATIONS_DATA
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching all medications: {e}",
        )


async def get_medication_by_id(id: str) -> Optional[FixedMedication]:

    for med in FIXED_MEDICATIONS_DATA:
        if med.id == id:
            return med
    raise HTTPException(status_code=404, detail=f"Medication with ID {id} not found")
