from fastapi import HTTPException, status, Depends
from auth.hashing import Hash
from auth.jwttoken import create_access_token, verify_token
from bson import ObjectId
from models.user import UserResponse, UserCreate
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Decodes and verifies the JWT token, returning the full user payload.
    Expects the token payload to include at least "id", "sub", and "role".
    """
    return verify_token(
        token,
        credentials_exception=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ),
    )


def require_roles(required_roles: List[str]):
    """
    Dependency that ensures the user has one of the required roles.
    Returns the full user payload if the check passes.
    """

    def dependency(user: Dict = Depends(get_current_user)) -> Dict:
        if user.get("role") not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        return user

    return dependency


def get_user_role(token: str = Depends(oauth2_scheme)):
    """Extracts the user’s role from the JWT token."""
    user_data = verify_token(
        token,
        credentials_exception=HTTPException(
            status_code=401, detail="Invalid credentials"
        ),
    )
    return user_data.get("role")


def check_permissions(required_roles: list):
    """Ensures the user has the necessary role for the requested resource."""

    def _check_permissions(token: str = Depends(oauth2_scheme)):
        user_role = get_user_role(token)
        if user_role not in required_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return user_role

    return _check_permissions


# Register User
async def register_user(db: AsyncIOMotorDatabase, user: UserCreate) -> UserResponse:
    existing_user = await db["users"].find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

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
        data={"id": str(user["_id"]), "sub": user["email"], "role": user["role"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user["email"]
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

    return UserResponse(**user)


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


# Delete User (Delete)
async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> dict:
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db["users"].delete_one({"_id": ObjectId(user_id)})
    return {"res": f"User with ID {user_id} deleted successfully"}


# Get All Users (with optional filters)
async def get_all_users(
    db: AsyncIOMotorDatabase, name=None, status=None, role=None
) -> List[UserResponse]:
    filters = {}
    if name:
        filters["name"] = name
    if status:
        filters["status"] = status
    if role:
        filters["role"] = role

    users_cursor = db["users"].find(filters)
    users = []
    async for user in users_cursor:
        users.append(UserResponse(**user))
    return users


async def get_user_by_email_service(db: AsyncIOMotorDatabase, email: str) -> dict:
    """
    Query the database for a user by email.
    """
    user = await db["users"].find_one({"email": email})
    if user:
        # Convert ObjectId to string
        user["_id"] = str(user["_id"])
        return user
    return None
