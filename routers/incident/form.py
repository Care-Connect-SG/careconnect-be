from typing import List
from fastapi import APIRouter, Depends
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

router = APIRouter(prefix="/incident/forms", tags=["Incident Management Subsystem"])


@router.post("/", summary="Create a new incident form", response_model=str)
async def create_new_form(form: FormCreate, db=Depends(get_db)):
    return await create_form(form, db)


@router.get(
    "/", summary="Retrieve all incident forms", response_model=List[FormResponse],  response_model_by_alias=False
)
async def list_forms(db=Depends(get_db)):
    return await get_forms(db)


@router.get(
    "/{form_id}", summary="Retrieve a specific form by Id", response_model=FormResponse,  response_model_by_alias=False
)
async def get_single_form(form_id: str, db=Depends(get_db)):
    form = await get_form_by_id(form_id, db)
    return form


@router.put("/{form_id}", summary="Update an existing form", response_model=str)
async def update_single_form(form_id: str, form: FormCreate, db=Depends(get_db)):
    return await update_form_fields(form_id, form, db)


@router.put("/{form_id}/publish", summary="Publish a draft form", response_model=str)
async def publish_draft_form(form_id: str, db=Depends(get_db)):
    return await update_form_status(form_id, db)


@router.delete("/{form_id}", summary="Delete a form", response_model=None)
async def delete_form(form_id: str, db=Depends(get_db)):
    return await remove_form(form_id, db)
