from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from api.auth.hashing import Hash
from api.auth.jwttoken import create_access_token
from api.auth.oauth import get_current_user
from config import settings
from models.user import User


# Define a lifespan method for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the database connection
    await startup_db_client(app)
    yield
    # Close the database connection
    await shutdown_db_client(app)


# Method to start the MongoDB connection
async def startup_db_client(app):
    app.mongodb_client = AsyncIOMotorClient(settings.mongo_uri)
    app.mongodb = app.mongodb_client["careconnect"]
    print("MongoDB connected.")


# Method to close the database connection
async def shutdown_db_client(app):
    app.mongodb_client.close()
    print("Database disconnected.")


app = FastAPI(lifespan=lifespan)

# CORS Middleware
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root(current_user: User = Depends(get_current_user)):
    return {"data": "Hello World"}


@app.post("/register")
async def create_user(request: User):
    db = app.mongodb  # Get the database instance
    existing_user = await db["users"].find_one({"username": request.username})

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pass = Hash.bcrypt(request.password)
    user_object = request.dict()
    user_object["password"] = hashed_pass

    await db["users"].insert_one(user_object)
    return {"res": "User created successfully"}


@app.post("/login")
async def login(request: OAuth2PasswordRequestForm = Depends()):
    db = app.mongodb  # Get the database instance
    user = await db["users"].find_one({"username": request.username})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user found with this username",
        )

    if not Hash.verify(user["password"], request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong username or password",
        )

    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}
