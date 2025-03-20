from fastapi import HTTPException, status, Depends
from auth.hashing import Hash
from auth.jwttoken import create_access_token, create_refresh_token, verify_token
from bson import ObjectId
from models.user import UserTagResponse, UserResponse, UserCreate, UserPasswordUpdate
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Optional
from db.connection import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Decodes and verifies the JWT token, returning the user ID and email.
    """
    return verify_token(
        token,
        credentials_exception=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ),
    )


class RoleChecker:
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles

    async def __call__(
        self,
        db: AsyncIOMotorDatabase = Depends(get_db),
        user: Dict = Depends(get_current_user)
    ) -> Dict:
        user_data = await db["users"].find_one(
            {"_id": ObjectId(user["id"])},
            {"role": 1}
        )
        if not user_data or user_data.get("role") not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        return user

def require_roles(required_roles: List[str]):
    return RoleChecker(required_roles)


async def get_user_role(
    db: AsyncIOMotorDatabase = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> str:
    """Fetches the user's role from the database using the token's user ID."""
    user_data = verify_token(
        token,
        credentials_exception=HTTPException(
            status_code=401,
            detail="Invalid credentials"
        ),
    )
    user = await db["users"].find_one(
        {"_id": ObjectId(user_data["id"])},
        {"role": 1}
    )
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user.get("role")


# Register User
async def register_user(db: AsyncIOMotorDatabase, user: UserCreate) -> UserResponse:
    existing_user = await db["users"].find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )

    hashed_pass = Hash.bcrypt(user.password)
    user_dict = user.model_dump(exclude_none=True)
    user_dict["password"] = hashed_pass
    user_dict["_id"] = ObjectId()
    await db["users"].insert_one(user_dict)

    return UserResponse(**user_dict)


# Login User (Authenticate)
async def login_user(db: AsyncIOMotorDatabase, username: str, password: str) -> dict:
    user = await db["users"].find_one({"email": username})
    if not user or not Hash.verify(user["password"], password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(
        data={"id": str(user["_id"]), "sub": user["email"]}
    )
    refresh_token = create_refresh_token(
        data={"id": str(user["_id"]), "sub": user["email"]}
    )

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# Get User by ID (Read)
async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> UserResponse:
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = await db["users"].find_one({"_id": user_object_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert _id to string for the response
    user["id"] = str(user["_id"])
    del user["_id"]
    return UserResponse(**user)


# Get User by Email
async def get_user_by_email_service(
    db: AsyncIOMotorDatabase, email: str
) -> Optional[UserResponse]:
    user = await db["users"].find_one({"email": email})
    if user:
        return UserResponse(**user)
    return None


# Update User (Update)
async def update_user(
    db: AsyncIOMotorDatabase, user_id: str, user_data: dict
) -> UserResponse:
    existing_user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    if "password" in user_data:
        user_data["password"] = Hash.bcrypt(user_data["password"])

    await db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": user_data})
    updated_user = await db["users"].find_one({"_id": ObjectId(user_id)})
    return UserResponse(**updated_user)


# Update User Password
async def update_user_password_service(
    db, user_id: str, password_data: UserPasswordUpdate
) -> UserResponse:
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )

    user = await db["users"].find_one({"_id": user_object_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not Hash.verify(user["password"], password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    try:
        new_hashed_password = Hash.bcrypt(password_data.new_password)
    except Exception as e:
        print("Error hashing new password:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error hashing new password",
        )

    result = await db["users"].update_one(
        {"_id": user_object_id}, {"$set": {"password": new_hashed_password}}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password update failed",
        )

    updated_user = await db["users"].find_one({"_id": user_object_id})
    return UserResponse(**updated_user)


# Delete User (Delete)
async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> dict:
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db["users"].delete_one({"_id": ObjectId(user_id)})
    return {"res": f"User with ID {user_id} deleted successfully"}


# Get All Users (with optional filters)
async def get_all_users(
    db: AsyncIOMotorDatabase,
    name=None,
    status=None,
    role=None,
    email: Optional[str] = None,
) -> List[UserResponse]:
    filters = {}
    if name:
        filters["name"] = name
    if status:
        filters["status"] = status
    if role:
        filters["role"] = role
    if email:
        filters["email"] = email

    users_cursor = db["users"].find(filters)
    users = []
    async for user in users_cursor:
        users.append(UserResponse(**user))
    return users


# Search for caregiver by name - for use in report tagging
async def get_caregiver_tags(search_key: str, limit: int, db) -> List[UserTagResponse]:
    if search_key:
        cursor = (
            db["users"]
            .find(
                {"name": {"$regex": search_key, "$options": "i"}},
                {"_id": 1, "name": 1, "role": 1},
            )
            .limit(limit)
        )
    else:
        cursor = db["users"].find()

    caregivers = []
    async for record in cursor:
        record["id"] = str(record["_id"])
        del record["_id"]
        caregivers.append(record)
    return caregivers


# Get Assigned To Name
async def get_assigned_to_name(db, assigned_to_id: str) -> str:
    user = await db.users.find_one({"_id": ObjectId(assigned_to_id)}, {"name": 1})
    return user["name"] if user and "name" in user else "Unknown"
