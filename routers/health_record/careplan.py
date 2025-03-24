from fastapi import APIRouter, Depends, Request, status
from models.careplan import CarePlanCreate, CarePlanResponse
from typing import List
from services.careplan_service import (
    create_careplan,
    get_careplans_by_resident,
    get_careplan_by_id,
    update_careplan,
    delete_careplan,
)
from db.connection import get_db
from utils.limiter import limiter

router = APIRouter(prefix="/residents/{resident_id}/careplan", tags=["Careplan"])


@router.post("/", response_model=CarePlanResponse, response_model_by_alias=False)
@limiter.limit("10/minute")
async def add_careplan(
    request: Request, resident_id: str, careplan: CarePlanCreate, db=Depends(get_db)
):
    return await create_careplan(db, resident_id, careplan)


@router.get("/", response_model=List[CarePlanResponse], response_model_by_alias=False)
@limiter.limit("100/minute")
async def list_careplans(request: Request, resident_id: str, db=Depends(get_db)):
    return await get_careplans_by_resident(db, resident_id)


@router.get(
    "/{careplan_id}", response_model=CarePlanResponse, response_model_by_alias=False
)
@limiter.limit("100/minute")
async def get_careplan(
    request: Request, resident_id: str, careplan_id: str, db=Depends(get_db)
):
    return await get_careplan_by_id(db, resident_id, careplan_id)


@router.put(
    "/{careplan_id}", response_model=CarePlanResponse, response_model_by_alias=False
)
@limiter.limit("10/minute")
async def update_careplan_record(
    request: Request,
    resident_id: str,
    careplan_id: str,
    update_data: CarePlanCreate,
    db=Depends(get_db),
):
    return await update_careplan(db, resident_id, careplan_id, update_data)


@router.delete("/{careplan_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_careplan_record(
    request: Request, resident_id: str, careplan_id: str, db=Depends(get_db)
):
    return await delete_careplan(db, resident_id, careplan_id)
