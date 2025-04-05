from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from db.connection import lifespan
from routers.activity import router as activity_router
from routers.cloudinary.image import router as image_router
from routers.group import router as group_router
from routers.health_record.careplan import router as careplan_router
from routers.health_record.fixed_medication import \
    router as fixed_medication_router
from routers.health_record.medical_history import \
    router as medical_history_router
from routers.health_record.medication import router as medication_router
from routers.health_record.medication_log import \
    router as medication_log_router
from routers.health_record.medication_public import \
    router as medication_public_router
from routers.health_record.wellness_report import \
    router as wellness_report_router
from routers.incident.form import router as form_router
from routers.incident.report import router as report_router
from routers.resident import router as resident_router
from routers.tag import router as tag_router
from routers.task import router as task_router
from routers.user import router as user_router
from utils.config import FE_URL
from utils.limiter import limiter

app = FastAPI(root_path="/api/v1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(group_router)
app.include_router(task_router)
app.include_router(resident_router)
app.include_router(medication_router)
app.include_router(form_router)
app.include_router(report_router)
app.include_router(tag_router)
app.include_router(careplan_router)
app.include_router(activity_router)
app.include_router(medical_history_router)
app.include_router(image_router)
app.include_router(fixed_medication_router)
app.include_router(wellness_report_router)
app.include_router(medication_log_router)
app.include_router(medication_public_router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
def read_root():
    return {"status": "Server is healthy"}
