from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from routers.limiter import limiter
from routers.user import router as user_router
from routers.group import router as group_router
from routers.task import router as task_router
from routers.resident import router as resident_router
from routers.medication import router as medication_router
from db.connection import lifespan
from config import FE_URL
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from bearer import verify_bearer_token

app = FastAPI(
    root_path="/api/v1", lifespan=lifespan, dependencies=[Depends(verify_bearer_token)]
)
# app = FastAPI(root_path="/api/v1")

# CORS Middleware
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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
def read_root():
    return {"status": "Server is healthy"}
