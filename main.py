# import fast api
from fastapi import FastAPI, HTTPException

from models import User # import the user model defined by us

# imports for the MongoDB database connection
from motor.motor_asyncio import AsyncIOMotorClient

# import for fast api lifespan
from contextlib import asynccontextmanager

from typing import List # Supports for type hints

from pydantic import BaseModel # Most widely used data validation library for python

from .config import settings

# define a lifespan method for fastapi
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the database connection
    await startup_db_client(app)
    yield
    # Close the database connection
    await shutdown_db_client(app)

# method for start the MongoDb Connection
async def startup_db_client(app):
    app.mongodb_client = AsyncIOMotorClient(
        settings.mongo_uri) # Replace with your connection string
    app.mongodb = app.mongodb_client.get_database("college")
    print("MongoDB connected.")

# method to close the database connection
async def shutdown_db_client(app):
    app.mongodb_client.close()
    print("Database disconnected.")

# creating a server with python FastAPI
app = FastAPI(lifespan=lifespan)

# hello world endpoint
@app.get("/")
def read_root():  # function that is binded with the endpoint
    return {"Hello": "World"}

# C <=== Create
@app.post("/api/v1/create-user", response_model=User)
async def insert_user(user: User):
    result = await app.mongodb["users"].insert_one(user.dict())
    inserted_user = await app.mongodb["users"].find_one({"_id": result.inserted_id})
    return inserted_user

# R <=== Read
# Read all users
@app.get("/api/v1/read-all-users", response_model=List[User])
async def read_users():
    users = await app.mongodb["users"].find().to_list(None)
    return users

# Read one user by email_address
@app.get("/api/v1/read-user/{email_address}", response_model=User)
async def read_user_by_email(email_address: str):
    user = await app.mongodb["users"].find_one({"email_address": email_address})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# U <=== Update
# Update user

class UpdateUserDTO(BaseModel):
    other_names: List[str] = None
    age: int = None
    # Include other fields as needed, with defaults to None or use the exclude_unset=True option

@app.put("/api/v1/update-user/{email_address}", response_model=User)
async def update_user(email_address: str, user_update: UpdateUserDTO):
    updated_result = await app.mongodb["users"].update_one(
        {"email_address": email_address}, {"$set": user_update.dict(exclude_unset=True)})
    if updated_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found or no update needed")
    updated_user = await app.mongodb["users"].find_one({"email_address": email_address})
    return updated_user

# D <=== Delete
# Delete user by email_address
@app.delete("/api/v1/delete-user/{email_address}", response_model=dict)
async def delete_user_by_email(email_address: str):
    delete_result = await app.mongodb["users"].delete_one({"email_address": email_address})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
