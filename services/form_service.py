from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import HTTPException

from models.form import FormCreate, FormResponse


async def create_form(form: FormCreate, db, currentUserId: str) -> str:
    form_data = form.model_dump()
    form_data["creator_id"] = ObjectId(currentUserId)
    form_data["created_at"] = datetime.now(timezone.utc)
    result = await db["forms"].insert_one(form_data)
    return str(result.inserted_id)


async def get_forms(status: str, db) -> List[FormResponse]:
    query = {}
    if status:
        query["status"] = status
    cursor = db["forms"].find(query)
    forms = []
    async for form in cursor:
        forms.append(form)
    return [FormResponse(**form) for form in forms]


async def get_form_by_id(form_id: str, db):
    try:
        object_id = ObjectId(form_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid form ID format")

    form_data = await db["forms"].find_one({"_id": object_id})
    if not form_data:
        raise HTTPException(status_code=404, detail="Form not found")
    return FormResponse(**form_data)


async def update_form_fields(form_id: str, form: FormCreate, db) -> str:
    try:
        object_id = ObjectId(form_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid form ID")

    form_data = await db["forms"].find_one({"_id": object_id})
    if not form_data:
        raise HTTPException(status_code=404, detail="Form not found")

    if form_data.get("status") == "Published":
        raise HTTPException(status_code=400, detail="Cannot modify a published form")

    update_data = form.model_dump(exclude_unset=True)
    await db["forms"].update_one({"_id": object_id}, {"$set": update_data})
    return form_id


async def update_form_status(form_id: str, db) -> str:
    try:
        object_id = ObjectId(form_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid form ID format")

    form_data = await db["forms"].find_one({"_id": object_id})
    if not form_data:
        raise HTTPException(status_code=404, detail="Form not found")

    await db["forms"].update_one({"_id": object_id}, {"$set": {"status": "Published"}})
    return form_id


async def remove_form(form_id: str, db):
    try:
        result = await db["forms"].delete_one({"_id": ObjectId(form_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Form not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid form ID")
