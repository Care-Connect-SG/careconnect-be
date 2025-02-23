from fastapi import Depends, APIRouter, Request, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from db.connection import get_db
from models.user import User, Token
from .limiter import limiter
from services.user_service import register_user, login_user

router = APIRouter(prefix="/users")

@router.post("/register")
@limiter.limit("1/second")
async def create_user(request: Request, user: User, db=Depends(get_db)):
    return await register_user(db, user)

@router.post("/login", response_model=Token)
@limiter.limit("1/second")
async def login(request: Request, db=Depends(get_db)):
    # Manually parse the form data from the request
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username/email and password are required."
        )

    # Call your login service function
    token = await login_user(db, username, password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials."
        )
    return token
