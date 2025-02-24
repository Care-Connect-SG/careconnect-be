# MongoDB Connection
from fastapi import FastAPI, HTTPException, Request
# from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

db = None

# Dependency for getting DB
async def get_db():
    try:
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client.get_database("caregiver")
        # Test the connection
        await db.command("ping")
        print("✅ Connected to MongoDB Atlas")
        yield db
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")
    finally:
        client.close()
        print("🛑 Database disconnected.")

# to be used in main.py when server is able to persist db connection
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     try:
#         app.mongodb_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
#         app.mongodb = app.mongodb_client.get_database("caregiver")
#         await app.mongodb.command("ping")
#         print("✅ Connected to MongoDB Atlas")
#         yield
#     except Exception as e:
#         print(f"❌ Database connection failed: {e}")
#         raise HTTPException(status_code=500, detail="Database connection error")
#     finally:
#         if hasattr(app, "mongodb_client"):
#             app.mongodb_client.close()
#             print("🛑 Database disconnected.")
