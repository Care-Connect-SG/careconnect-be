from fastapi import Depends, APIRouter, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from db.connection import get_db
from models.user import User, Token
from services.user_service import check_permissions, register_user, login_user, get_user_by_id, get_all_users, update_user, delete_user
from .limiter import limiter


router = APIRouter(prefix="/users")

# Create User (Register)
@router.post("/register", response_model=User)
@limiter.limit("10/second")
async def create_user(request: Request, user: User, db=Depends(get_db)):
    try:
        return await register_user(db, user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error registering user: {str(e)}")

# User Login
@router.post("/login", response_model=Token)
@limiter.limit("10/second")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    try:
        return await login_user(db, form_data.username, form_data.password)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Get all users
@router.get("/", response_model=list[User])
@limiter.limit("5/second")
async def get_users(request: Request, db=Depends(get_db)):
    try:
        users = await get_all_users(db)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

# Get user by ID
@router.get("/{user_id}", response_model=User)
@limiter.limit("5/second")
async def get_user(request: Request, user_id: str, db=Depends(get_db)):
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

# Update User Details
@router.put("/{user_id}", response_model=User)
@limiter.limit("5/second")
async def update_user_details(request: Request, user_id: str, user: User, db=Depends(get_db)):
    try:
        updated_user = await update_user(db, user_id, user)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating user: {str(e)}")

# Delete User
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/second")
async def delete_user_by_id(request: Request, user_id: str, db=Depends(get_db)):
    try:
        success = await delete_user(db, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

