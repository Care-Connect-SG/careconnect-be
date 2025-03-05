from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from utils.config import MONGO_URI


async def get_db(request: Request):
    return request.app.mongodb


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.mongodb_client = AsyncIOMotorClient(
            MONGO_URI, serverSelectionTimeoutMS=5000
        )
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
