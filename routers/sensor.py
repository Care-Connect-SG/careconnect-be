from fastapi import APIRouter, Request, Depends
from db.connection import get_resident_db
from services.fall_detection_service import create_fall_log
from models.fall_detection import FallLogCreate
import math
from datetime import datetime, timedelta

sensor_router = APIRouter()

FALL_ACCEL_THRESHOLD = 4.0  # g
POST_FALL_INACTIVITY_WINDOW = 2  # seconds
POST_FALL_ACCEL_THRESHOLD = 0.5  # g
FALL_COOLDOWN_SECONDS = 10  # Prevent duplicate logs

last_accel_spike = None
last_fall_logged_time = None

@sensor_router.post("/sensor-data")
async def receive_sensor_data(request: Request, db=Depends(get_resident_db)):
    global last_accel_spike, last_fall_logged_time

    data = await request.json()
    try:
        ax = float(data.get("accelerometerAccelerationX", 0))
        ay = float(data.get("accelerometerAccelerationY", 0))
        az = float(data.get("accelerometerAccelerationZ", 0))
        accel_mag = math.sqrt(ax**2 + ay**2 + az**2)

        print(f"📡 Accel: {accel_mag:.3f}g")

        now = datetime.utcnow()

        # Step 1: Detect sudden spike in acceleration
        if accel_mag > FALL_ACCEL_THRESHOLD:
            # If we already detected a fall recently, skip this
            if last_fall_logged_time and (now - last_fall_logged_time).total_seconds() < FALL_COOLDOWN_SECONDS:
                print("⚠️ Fall already logged recently — skipping")
                return {"status": "cooldown"}

            last_accel_spike = {
                "timestamp": now,
            }
            print("💥 Impact detected — waiting to confirm fall...")
            print("💥💥💥💥💥💥💥💥💥💥")

        # Step 2: Post-impact confirmation based on inactivity
        if last_accel_spike:
            time_since_spike = (now - last_accel_spike["timestamp"]).total_seconds()

            if 0 < time_since_spike <= POST_FALL_INACTIVITY_WINDOW:
                if accel_mag < POST_FALL_ACCEL_THRESHOLD:
                    print(f"🤔 Low movement post-impact ({accel_mag:.2f}g)")
            elif time_since_spike > POST_FALL_INACTIVITY_WINDOW:
                print("🚨 FALL CONFIRMED — Logging to DB!")
                fall_log = FallLogCreate(
                    resident_id="68015e726aafe2290598b8a4",
                    device_id="mock_wearable_12345",
                    acceleration_magnitude=accel_mag,
                    status="pending",
                    incident_report_id=None,
                )
                await create_fall_log(db, fall_log)
                
                last_fall_logged_time = now  # 🧠 Update cooldown timer
                last_accel_spike = None

        return {"status": "ok"}

    except Exception as e:
        print("❌ Error parsing sensor data:", e)
        return {"status": "error", "details": str(e)}
