from fastapi import Depends, APIRouter, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from db.connection import get_db
from models.user import UserCreate, UserResponse, Token, RefreshTokenRequest
from auth.jwttoken import refresh_access_token
from services.user_service import (
    get_user_role,
    get_user_by_email_service,
    register_user,
    login_user,
    get_user_by_id,
    get_all_users,
    update_user,
    delete_user,
)
from utils.limiter import limiter
from typing import List, Optional

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def create_user(request: Request, user_data: UserCreate, db=Depends(get_db)):
    user = await register_user(db, user_data)
    return {"message": "User registered successfully"}


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    token = await login_user(db, form_data.username, form_data.password)
    return token


@router.get("/", response_model=List[UserResponse], response_model_by_alias=False)
@limiter.limit("100/minute")
async def get_users(request: Request, email: Optional[str] = None, db=Depends(get_db)):
    users = await get_all_users(email=email, db=db)
    return users


@router.get("/{user_id}", response_model=UserResponse, response_model_by_alias=False)
@limiter.limit("100/minute")
async def get_user(request: Request, user_id: str, db=Depends(get_db)):
    user = await get_user_by_id(db, user_id)
    return user


@router.put("/{user_id}", response_model=UserResponse, response_model_by_alias=False)
@limiter.limit("10/minute")
async def update_user_details(
    request: Request, user_id: str, user_data: UserCreate, db=Depends(get_db)
):
    updated_user = await update_user(
        db, user_id, user_data.model_dump(exclude_unset=True)
    )
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_user_by_id(request: Request, user_id: str, db=Depends(get_db)):
    await delete_user(db, user_id)


@router.get("/me/role")
@limiter.limit("10/minute")
async def get_current_user_role(request: Request, role: str = Depends(get_user_role)):
    return {"role": role}


@router.get("/email/{email}", status_code=status.HTTP_200_OK)
@limiter.limit("5/second")
async def get_user_by_email(request: Request, email: EmailStr, db=Depends(get_db)):
    """
    Fetch user by email from the database.
    """
    user = await get_user_by_email_service(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/refresh-token")
async def refresh_token_endpoint(payload: RefreshTokenRequest):
    return refresh_access_token(payload.refresh_token)
