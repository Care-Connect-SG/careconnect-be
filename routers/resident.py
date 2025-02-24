from fastapi import APIRouter, Depends, Request
from models.resident import RegistrationCreate
from services.residentRecord_service import create_residentInfo
from db.connection import get_db
from .limiter import limiter

router = APIRouter(prefix="/createResidentRecord", tags=["residentRecords"])

@router.post("/")
@limiter.limit("1/second")
async def register_registration(request: Request, registration: RegistrationCreate, db=Depends(get_db)):
    return await create_residentInfo(db, registration)
