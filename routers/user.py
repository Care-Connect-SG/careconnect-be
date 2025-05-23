from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from auth.jwttoken import refresh_access_token
from db.connection import get_db
from models.user import (
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)
from services.user_service import (
    delete_user,
    get_all_users,
    get_current_user,
    get_user_by_id,
    get_user_role,
    login_user,
    register_user,
    require_roles,
    update_user,
    update_user_password_service,
)
from utils.limiter import limiter

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def create_user(
    request: Request,
    user_data: UserCreate,
    db=Depends(get_db),
    user: dict = Depends(require_roles(["Admin"])),
):
    user = await register_user(db, user_data)
    return {"detail": "User registered successfully"}


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


@router.get("/me", response_model=UserResponse, response_model_by_alias=False)
# @limiter.limit("10/minute")
async def get_current_user_details(
    request: Request, current_user: Dict = Depends(get_current_user), db=Depends(get_db)
):
    user = await get_user_by_id(db, current_user["id"])
    return user


@router.get("/me/role")
# @limiter.limit("10/minute")
async def get_current_user_role(request: Request, role: str = Depends(get_user_role)):
    return {"role": role}


@router.get("/{user_id}", response_model=UserResponse, response_model_by_alias=False)
@limiter.limit("100/minute")
async def get_user(request: Request, user_id: str, db=Depends(get_db)):
    user = await get_user_by_id(db, user_id)
    return user


@router.put("/{user_id}", response_model=UserResponse, response_model_by_alias=False)
@limiter.limit("10/minute")
async def update_user_details(
    request: Request,
    user_id: str,
    user_data: UserUpdate,
    db=Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    if (current_user["role"] == "Admin") or (current_user["id"] == user_id):
        updated_user = await update_user(
            db, user_id, user_data.model_dump(exclude_unset=True)
        )
        return updated_user


@router.put("/me/password", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def update_password_endpoint(
    request: Request,
    password_data: UserPasswordUpdate,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db),
):
    updated_user = await update_user_password_service(
        db, current_user["id"], password_data
    )
    return {"detail": "Password updated successfully"}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_user_by_id(
    request: Request,
    user_id: str,
    db=Depends(get_db),
    user: dict = Depends(require_roles(["Admin"])),
):
    await delete_user(db, user_id)


@router.post("/refresh-token")
async def refresh_token_endpoint(payload: RefreshTokenRequest):
    return refresh_access_token(payload.refresh_token)
