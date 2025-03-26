from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from utils.config import MONGO_URI


async def get_db(request: Request):
    return request.app.primary_db


async def get_resident_db(request: Request):
    return request.app.secondary_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.mongodb_client = AsyncIOMotorClient(
            MONGO_URI, serverSelectionTimeoutMS=5000
        )
        app.primary_db = app.mongodb_client.get_database("caregiver")
        await app.primary_db.command("ping")
        print("✅ Connected to Caregiver MongoDB Atlas")

        app.secondary_db = app.mongodb_client.get_database("resident")
        await app.secondary_db.command("ping")
        print("✅ Connected to Resident MongoDB Atlas")

        yield
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    finally:
        if hasattr(app, "mongodb_client"):
            app.mongodb_client.close()
            print("🛑 Databases disconnected.")
