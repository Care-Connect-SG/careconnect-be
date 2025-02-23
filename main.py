from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.limiter import limiter
from routers.user import router as user_router
from db.connection import lifespan
from config import FE_URL
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI(lifespan=lifespan)

# CORS Middleware
origins = [
    FE_URL,
    "https://careconnect-fe.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
def read_root():
    return {"status": "Server is healthy"}
