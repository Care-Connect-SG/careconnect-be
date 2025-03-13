from typing import List, Optional
from fastapi import APIRouter, Depends, Request

from db.connection import get_db
from models.resident import ResidentTagResponse
from models.user import UserTagResponse
from services.resident_service import get_resident_tags
from services.user_service import get_caregiver_tags
from utils.limiter import limiter


router = APIRouter(prefix="/tags", tags=["Resident and Caregiver Tags"])


@router.get(
    "/residents",
    response_model=List[ResidentTagResponse],
    response_model_by_alias=False,
)
@limiter.limit("100/minute")
async def search_resident_tags(
    request: Request,
    search_key: Optional[str] = None,
    limit: int = 10,
    db=Depends(get_db),
):
    return await get_resident_tags(search_key, limit, db)


@router.get("/caregivers", response_model=List[UserTagResponse])
@limiter.limit("100/minute")
async def search_users_by_name(
    request: Request,
    search_key: Optional[str] = None,
    limit: int = 10,
    db=Depends(get_db),
):
    return await get_caregiver_tags(search_key, limit, db)
