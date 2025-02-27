from fastapi import Depends, HTTPException, status
from auth.hashing import Hash
from auth.jwttoken import create_access_token, verify_token
from bson import ObjectId
from models.user import User
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def get_user_role(token: str = Depends(oauth2_scheme)):
    """ Extracts the user’s role from the JWT token. """
    user_data = verify_token(token, credentials_exception=HTTPException(status_code=401, detail="Invalid credentials"))
    return user_data.get("role")


def check_permissions(required_roles: list):
    """ Ensures the user has the necessary role for the requested resource. """
    def _check_permissions(token: str = Depends(oauth2_scheme)):
        user_role = get_user_role(token)
        
        if user_role not in required_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return user_role
    
    return _check_permissions


async def register_user(db, user: User):
    existing_user = await db["users"].find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_pass = Hash.bcrypt(user.password)
    user_dict = user.model_dump(exclude_none=True)
    user_dict["_id"] = ObjectId() 
    user_dict = user.model_dump()
    user_dict["password"] = hashed_pass

    result = await db["users"].insert_one(user_dict)

    return user_dict


# 2. Login User (Authenticate)
async def login_user(db, username: str, password: str):
    user = await db["users"].find_one({"email": username})
    if not user or not Hash.verify(user["password"], password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(data={"sub": user["email"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user["email"]
    }


# 3. Get User by ID (Read)
async def get_user_by_id(db, user_id: str) -> User:
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = await db["users"].find_one({"_id": user_object_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = User(**user)
    return user_data


# 4. Update User (Update)
async def update_user(db, user_id: str, user_data: dict) -> User:
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # If password is being updated, hash it
    if "password" in user_data:
        user_data["password"] = Hash.bcrypt(user_data["password"])

    await db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": user_data})

    updated_user = await db["users"].find_one({"_id": ObjectId(user_id)})

    return User(**updated_user)


# 5. Delete User (Delete)
async def delete_user(db, user_id: str) -> dict:
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db["users"].delete_one({"_id": ObjectId(user_id)})

    return {"res": f"User with ID {user_id} deleted successfully"}


async def get_all_users(db: AsyncIOMotorDatabase, name=None, status=None, role=None):
    """Retrieve all users from the database with optional filters"""
    filters = {}
    if name:
        filters["name"] = name
    if status:
        filters["status"] = status
    if role:
        filters["role"] = role

    users = await db["users"].find(filters).to_list(length=100)
    return [{"id": str(user["_id"]), **user} for user in users]
