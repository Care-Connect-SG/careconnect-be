from fastapi import APIRouter, Request, Depends
from db.connection import get_resident_db
from services.fall_detection_service import create_fall_log
from models.fall_detection import FallLogCreate
import math
from datetime import datetime

sensor_router = APIRouter()

FALL_ACCEL_THRESHOLD = 2.5  # g
FALL_GYRO_THRESHOLD = 2.0  # rad/s

RESIDENT_ID = "67bd9832c775476225864ac7"
DEVICE_ID = "mock_wearable_12345"


@sensor_router.post("/sensor-data")
async def receive_sensor_data(request: Request, db=Depends(get_resident_db)):
    data = await request.json()

    try:
        # Acceleration
        ax = float(data.get("accelerometerAccelerationX", 0))
        ay = float(data.get("accelerometerAccelerationY", 0))
        az = float(data.get("accelerometerAccelerationZ", 0))
        accel_mag = math.sqrt(ax**2 + ay**2 + az**2)

        # Gyroscope
        gx = float(data.get("gyroRotationX", 0))
        gy = float(data.get("gyroRotationY", 0))
        gz = float(data.get("gyroRotationZ", 0))
        gyro_mag = math.sqrt(gx**2 + gy**2 + gz**2)

        print(f"📡 Accel: {accel_mag:.3f}g | Gyro: {gyro_mag:.3f}rad/s")

        # Detect fall directly
        if accel_mag > FALL_ACCEL_THRESHOLD and gyro_mag > FALL_GYRO_THRESHOLD:
            print("🚨 FALL DETECTED — Logging to DB!")

            fall_log = FallLogCreate(
                resident_id=RESIDENT_ID,
                device_id=DEVICE_ID,
                acceleration_magnitude=accel_mag,
                gyro_rotation={"x": gx, "y": gy, "z": gz},
                status="pending",
                incident_report_id=None,
            )

            await create_fall_log(db, fall_log)

        return {"status": "ok"}

    except Exception as e:
        print("❌ Error parsing sensor data:", e)
        return {"status": "error", "details": str(e)}
