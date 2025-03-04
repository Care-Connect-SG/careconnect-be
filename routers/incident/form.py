from typing import List
from fastapi import APIRouter, Depends, Request
from db.connection import get_db
from models.form import FormCreate, FormResponse
from services.form_service import (
    create_form,
    get_forms,
    get_form_by_id,
    update_form_fields,
    update_form_status,
    remove_form,
)
from utils.limiter import limiter

router = APIRouter(prefix="/incident/forms", tags=["Incident Management Subsystem"])


@router.post("/", summary="Create a new incident form", response_model=str)
@limiter.limit("10/minute")
async def create_new_form(request: Request, form: FormCreate, db=Depends(get_db)):
    return await create_form(form, db)


@router.get(
    "/",
    summary="Retrieve all incident forms",
    response_model=List[FormResponse],
    response_model_by_alias=False,
)
@limiter.limit("100/minute")
async def list_forms(request: Request, db=Depends(get_db)):
    return await get_forms(db)


@router.get(
    "/{form_id}",
    summary="Retrieve a specific form by Id",
    response_model=FormResponse,
    response_model_by_alias=False,
)
@limiter.limit("100/minute")
async def get_single_form(request: Request, form_id: str, db=Depends(get_db)):
    return await get_form_by_id(form_id, db)


@router.put("/{form_id}", summary="Update an existing form", response_model=str)
@limiter.limit("10/minute")
async def update_single_form(
    request: Request, form_id: str, form: FormCreate, db=Depends(get_db)
):
    return await update_form_fields(form_id, form, db)


@router.put("/{form_id}/publish", summary="Publish a draft form", response_model=str)
@limiter.limit("10/minute")
async def publish_draft_form(request: Request, form_id: str, db=Depends(get_db)):
    return await update_form_status(form_id, db)


@router.delete("/{form_id}", summary="Delete a form", response_model=None)
@limiter.limit("10/minute")
async def delete_form(request: Request, form_id: str, db=Depends(get_db)):
    return await remove_form(form_id, db)
