from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.limiter import limiter
from routers.user import router as user_router
from routers.group import router as group_router
from routers.task import router as task_router
from routers.resident import router as resident_router
from routers.medication import router as medication_router
from routers.careplan import router as careplan_router
from routers.incident.form import router as form_router
from routers.incident.report import router as report_router
from routers.tag import router as tag_router
from routers.medical_history import router as medicalHistory_router
from db.connection import lifespan
from utils.config import FE_URL
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

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
app.include_router(medicalHistory_router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
def read_root():
    return {"status": "Server is healthy"}
