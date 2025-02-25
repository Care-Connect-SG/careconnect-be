from fastapi import Depends, APIRouter, Request
from fastapi.security import OAuth2PasswordRequestForm
from db.connection import get_db
from models.user import User, Token
from .limiter import limiter
from services.user_service import register_user, login_user

router = APIRouter(prefix="/users")

@router.post("/register")
@limiter.limit("10/second")
async def create_user(request: Request, user: User, db=Depends(get_db)):
    return await register_user(db, user)

@router.post("/login", response_model=Token)
@limiter.limit("10/second")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    return await login_user(db, form_data.username, form_data.password)
