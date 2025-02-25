from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.limiter import limiter
from routers.user import router as user_router
from routers.task import router as task_router
from db.connection import lifespan
from config import FE_URL
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import pkg_resources

"""to be used when server is able to persist db connection (vercel is not able to do that because it is serverless)"""
app = FastAPI(lifespan=lifespan)

# app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(task_router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
def read_root():
    return {"status": "Server is healthy"}

@app.get("/versions")
def get_versions():
    fastapi_version = pkg_resources.get_distribution("fastapi").version
    uvicorn_version = pkg_resources.get_distribution("uvicorn").version
    # add other packages as needed
    return {
        "fastapi": fastapi_version,
        "uvicorn": uvicorn_version,
    }
