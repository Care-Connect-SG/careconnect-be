from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from api.auth.hashing import Hash
from api.auth.jwttoken import create_access_token
from api.auth.oauth import get_current_user
from models.user import User, Login, Token
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.mongodb_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        app.mongodb = app.mongodb_client.get_database("caregiver")
        await app.mongodb.command("ping")
        print("✅ Connected to MongoDB Atlas")
        yield
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    finally:
        if hasattr(app, "mongodb_client"):
            app.mongodb_client.close()
            print("🛑 Database disconnected.")

app = FastAPI(lifespan=lifespan)

# CORS Middleware
origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for getting DB
async def get_db(request: Request):
    return request.app.mongodb

@app.get("/")
def read_root():
    return {"status": "Server is healthy"}

@app.post("/register")
async def create_user(request: User, db=Depends(get_db)):
    existing_user = await db["users"].find_one({"email": request.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed_pass = Hash.bcrypt(request.password)
    user_object = request.dict()
    user_object["password"] = hashed_pass
    await db["users"].insert_one(user_object)
    return {"res": "User created successfully"}

@app.post("/login", response_model=Token)
async def login(request: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = await db["users"].find_one({"email": request.username})

    if not user or not Hash.verify(user["password"], request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(data={"sub": user["email"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user["email"]
    }



