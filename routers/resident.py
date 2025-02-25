from fastapi import APIRouter, Depends, Request, Query
from models.resident import RegistrationCreate, RegistrationResponse
from typing import List
from services.residentRecord_service import create_residentInfo, get_all_residents, get_residents_by_name
from db.connection import get_db
from .limiter import limiter

router = APIRouter(prefix="/residents", tags=["Resident Records"])

@router.post("/createNewRecord")
@limiter.limit("1/second")
async def create_resident_record(request: Request, registration: RegistrationCreate, db=Depends(get_db)):
    return await create_residentInfo(db, registration)

@router.get("/", response_model=List[RegistrationResponse])
@limiter.limit("1/second")
async def view_all_residents(request: Request, db=Depends(get_db)):
    return await get_all_residents(db)

@router.get("/search", response_model=List[RegistrationResponse])
@limiter.limit("1/second")
async def search_residents(request: Request, name: str = Query(..., description="Substring to search in resident names"), db=Depends(get_db)):

    return await get_residents_by_name(db, name)
