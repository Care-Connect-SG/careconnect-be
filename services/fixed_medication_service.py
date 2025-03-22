import datetime
from typing import List, Optional
from models.health_record.fixed_medication import FixedMedication

MEDICATIONS_DB = [
    FixedMedication(
        medication_id="1234567",
        medication_name="Aspirin",
        dosage="100mg",
        frequency="Twice a day",
        expiry_date=datetime.date(2025, 12, 31),
        instructions="Take with food",
    ),
    FixedMedication(
        medication_id="2345678",
        medication_name="Ibuprofen",
        dosage="200mg",
        frequency="Once a day",
        expiry_date=datetime.date(2025, 11, 15),
        instructions="Take after meals",
    ),
    FixedMedication(
        medication_id="3456789",
        medication_name="Paracetamol",
        dosage="500mg",
        frequency="Every 6 hours as needed",
        expiry_date=datetime.date(2026, 1, 20),
        instructions="Do not exceed 4g per day",
    ),
    FixedMedication(
        medication_id="3893809",
        medication_name="Paracetamol",
        dosage="500mg",
        frequency="Every 6 hours as needed",
        expiry_date=datetime.date(2026, 1, 20),
        instructions="Do not exceed 4g per day",
    ),
    FixedMedication(
        medication_id="5678901",
        medication_name="Amoxicillin",
        dosage="500mg",
        frequency="Every 8 hours",
        expiry_date=datetime.date(2025, 9, 30),
        instructions="Complete full course even if symptoms improve",
    ),
    FixedMedication(
        medication_id="6789012",
        medication_name="Atorvastatin",
        dosage="10mg",
        frequency="Once daily at bedtime",
        expiry_date=datetime.date(2027, 3, 10),
        instructions="Avoid grapefruit juice while taking this medication",
    ),
    FixedMedication(
        medication_id="7890123",
        medication_name="Metformin",
        dosage="500mg",
        frequency="Twice daily with meals",
        expiry_date=datetime.date(2026, 6, 25),
        instructions="Monitor blood sugar levels regularly",
    ),
]


def get_all_medications() -> List[FixedMedication]:
    return MEDICATIONS_DB


def get_medication_by_id(medication_id: str) -> Optional[FixedMedication]:
    for med in MEDICATIONS_DB:
        if med.medication_id == medication_id:
            return med
    return None
