from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request

from db.connection import get_resident_db
from models.resident import RegistrationCreate, RegistrationResponse, RegistrationUpdate
from services.resident_service import (
    create_residentInfo,
    delete_resident,
    get_all_residents,
    get_resident_by_id,
    get_residents_count_with_search,
    get_residents_with_pagination,
    update_resident,
)
from services.user_service import require_roles
from utils.limiter import limiter

router = APIRouter(prefix="/residents", tags=["Resident Records"])


@router.post("/createNewRecord")
@limiter.limit("10/minute")
async def create_resident_record(
    request: Request, registration: RegistrationCreate, db=Depends(get_resident_db)
):
    return await create_residentInfo(db, registration)


@router.get(
    "/getAllResidents",
    response_model=List[RegistrationResponse],
    response_model_by_alias=False,
)
@limiter.limit("100/minute")
async def list_all_residents(
    request: Request,
    db=Depends(get_resident_db),
):
    return await get_all_residents(db)


@router.get(
    "/",
    response_model=List[RegistrationResponse],
    response_model_by_alias=False,
)
@limiter.limit("100/minute")
async def list_residents_with_pagination(
    request: Request,
    db=Depends(get_resident_db),
    page: Optional[int] = 1,
    limit: Optional[int] = 8,
    search: Optional[str] = None,
):
    return await get_residents_with_pagination(db, page, limit, search)


@router.get("/count/numOfResidents", response_model=int)
@limiter.limit("100/minute")
async def get_count(
    request: Request,
    db=Depends(get_resident_db),
    search: Optional[str] = None,
):
    return await get_residents_count_with_search(db, search)


@router.get(
    "/{resident_id}", response_model=RegistrationResponse, response_model_by_alias=False
)
@limiter.limit("100/minute")
async def view_resident_by_id(
    request: Request, resident_id: str, db=Depends(get_resident_db)
):
    return await get_resident_by_id(db, resident_id)


@router.put(
    "/{resident_id}", response_model=RegistrationResponse, response_model_by_alias=False
)
@limiter.limit("10/minute")
async def update_resident_record(
    request: Request,
    resident_id: str,
    update_data: RegistrationUpdate,
    db=Depends(get_resident_db),
    current_user: Dict = Depends(require_roles(["Admin"])),
):
    return await update_resident(db, resident_id, update_data)


@router.delete("/{resident_id}")
@limiter.limit("10/minute")
async def delete_resident_record(
    request: Request, resident_id: str, db=Depends(get_resident_db)
):
    return await delete_resident(db, resident_id)
