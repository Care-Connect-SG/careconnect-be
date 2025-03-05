from fastapi import APIRouter, Depends, Request, Query
from models.resident import RegistrationCreate, RegistrationResponse
from typing import List, Optional
from services.resident_service import (
    create_residentInfo,
    get_all_residents,
    get_residents_by_name,
    get_resident_by_id,
    update_resident,
    delete_resident,
    get_all_residents_by_nurse
)
from db.connection import get_db
from .limiter import limiter

router = APIRouter(prefix="/residents", tags=["Resident Records"])


@router.post("/createNewRecord")
@limiter.limit("1/second")
async def create_resident_record(
    request: Request, registration: RegistrationCreate, db=Depends(get_db)
):
    return await create_residentInfo(db, registration)

@router.get("/", response_model=List[RegistrationResponse], response_model_by_alias=False)
@limiter.limit("1/second")
async def list_residents(
    request: Request,
    db=Depends(get_db),
    nurse: Optional[str] = None  # e.g. /residents?nurse=Alice
):
  
    if nurse:
        return await get_all_residents_by_nurse(db, nurse)
    else:
        return await get_all_residents(db)
@router.get(
    "/search", response_model=List[RegistrationResponse], response_model_by_alias=False
)
@limiter.limit("1/second")
async def search_residents(
    request: Request,
    name: str = Query(..., description="Substring to search in resident names"),
    db=Depends(get_db),
):
    return await get_residents_by_name(db, name)


@router.get(
    "/{resident_id}", response_model=RegistrationResponse, response_model_by_alias=False
)
@limiter.limit("1/second")
async def view_resident_by_id(request: Request, resident_id: str, db=Depends(get_db)):
    return await get_resident_by_id(db, resident_id)


@router.put(
    "/{resident_id}", response_model=RegistrationResponse, response_model_by_alias=False
)
@limiter.limit("1/second")
async def update_resident_record(
    request: Request,
    resident_id: str,
    update_data: RegistrationCreate,
    db=Depends(get_db),
):
    return await update_resident(db, resident_id, update_data)


@router.delete("/{resident_id}")
@limiter.limit("1/second")
async def delete_resident_record(
    request: Request, resident_id: str, db=Depends(get_db)
):
    return await delete_resident(db, resident_id)

