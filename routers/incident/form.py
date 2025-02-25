from fastapi import APIRouter, Depends, HTTPException
from db.connection import get_db
from models.form import FormBase
from services.form_service import (
    create_form,
    get_forms,
    get_form_by_id,
    update_form_fields,
    update_form_status,
    remove_form
)

router = APIRouter(prefix="/incident/forms", tags=["Incident Management Subsystem"])

@router.post("/")
async def create_new_form(form: FormBase, db=Depends(get_db)):
    return await create_form(form, db)

@router.get("/")
async def list_forms(db=Depends(get_db)):
    return await get_forms(db)

@router.get("/{form_id}")
async def get_single_form(form_id: str, db=Depends(get_db)):
    form = await get_form_by_id(form_id, db)
    return form

@router.put("/{form_id}")
async def update_single_form(form_id: str, form: FormBase, db=Depends(get_db)):
    return await update_form_fields(form_id, form, db)

@router.put("/{form_id}/publish")
async def publish_draft_form(form_id: str, form: FormBase, db=Depends(get_db)):
    return await update_form_status(form_id, form, db)

@router.delete("/{form_id}")
async def delete_form(form_id: str, db=Depends(get_db)):
    return await remove_form(form_id, db)
