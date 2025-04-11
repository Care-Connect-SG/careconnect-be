# from fastapi import APIRouter, Request
# import math

# sensor_router = APIRouter()
# FALL_ACCEL_THRESHOLD = 2.5  # g-force threshold

# @sensor_router.post("/sensor-data")
# async def receive_sensor_data(request: Request):
#     try:
#         data = await request.json()

#         ax = float(data.get("accelerometerAccelerationX", 0))
#         ay = float(data.get("accelerometerAccelerationY", 0))
#         az = float(data.get("accelerometerAccelerationZ", 0))

#         # Calculate magnitude of acceleration vector
#         accel_magnitude = math.sqrt(ax**2 + ay**2 + az**2)

#         print(f"📡 Accel Magnitude: {accel_magnitude:.3f}g")

#         if accel_magnitude > FALL_ACCEL_THRESHOLD:
#             print("🚨 FALL DETECTED based on acceleration threshold!")
#             print("\n" + "🚨" * 10)
#             print("🚨 FALL DETECTED based on acceleration threshold!")
#             print("\n" + "🚨" * 10)
            

#             # TODO: Trigger frontend alert via websocket or REST
#             # e.g. save to DB or push notification event

#         return {"status": "ok"}
#     except Exception as e:
#         print("Error parsing sensor data:", e)
#         return {"status": "error", "details": str(e)}
from fastapi import APIRouter, Request
import math
import time

sensor_router = APIRouter()

FALL_ACCEL_THRESHOLD = 2.5  # g
FALL_GYRO_THRESHOLD = 2.0   # rad/s
FALL_INACTIVITY_THRESHOLD = 0.2  # g
FALL_CONFIRMATION_TIME = 3  # seconds

# Store last fall event
last_fall_time = 0

@sensor_router.post("/sensor-data")
async def receive_sensor_data(request: Request):
    global last_fall_time
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

        # Check for potential fall
        if accel_mag > FALL_ACCEL_THRESHOLD and gyro_mag > FALL_GYRO_THRESHOLD:
            last_fall_time = time.time()
            print("🚨 FALL DETECTED based on acceleration threshold!")
            print("\n" + "🚨" * 10)
            print("🚨 FALL DETECTED based on acceleration threshold!")
            print("\n" + "🚨" * 10)
        # Confirm fall by checking for inactivity after impact
        elif last_fall_time != 0 and (time.time() - last_fall_time < FALL_CONFIRMATION_TIME):
            if accel_mag < FALL_INACTIVITY_THRESHOLD:
                print("✅ FALL CONFIRMED due to inactivity after impact.")
                last_fall_time = 0  # Reset
                # TODO: Signal frontend
        else:
            last_fall_time = 0  # No fall

        return {"status": "ok"}

    except Exception as e:
        print("❌ Error parsing sensor data:", e)
        return {"status": "error", "details": str(e)}
