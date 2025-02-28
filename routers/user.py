from fastapi import Depends, APIRouter, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from db.connection import get_db
from models.user import UserCreate, UserResponse, Token
from services.user_service import (
    register_user,
    login_user,
    get_user_by_id,
    get_all_users,
    update_user,
    delete_user,
)
from .limiter import limiter
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])


# Create User (Register)
@router.post(
    "/register",
    response_model=UserResponse,
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/second")
async def create_user(request: Request, user_data: UserCreate, db=Depends(get_db)):
    user = await register_user(db, user_data)
    return user


# User Login
@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
@limiter.limit("10/second")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    token = await login_user(db, form_data.username, form_data.password)
    return token


# Get all users
@router.get("/", response_model=List[UserResponse], response_model_by_alias=False)
@limiter.limit("5/second")
async def get_users(request: Request, db=Depends(get_db)):
    users = await get_all_users(db)
    return users


# Get user by ID
@router.get("/{user_id}", response_model=UserResponse, response_model_by_alias=False)
@limiter.limit("5/second")
async def get_user(request: Request, user_id: str, db=Depends(get_db)):
    user = await get_user_by_id(db, user_id)
    return user


# Update User Details (using UserCreate for a full update)
@router.put("/{user_id}", response_model=UserResponse, response_model_by_alias=False)
@limiter.limit("5/second")
async def update_user_details(
    request: Request, user_id: str, user_data: UserCreate, db=Depends(get_db)
):
    updated_user = await update_user(
        db, user_id, user_data.model_dump(exclude_unset=True)
    )
    return updated_user


# Delete User
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/second")
async def delete_user_by_id(request: Request, user_id: str, db=Depends(get_db)):
    await delete_user(db, user_id)
