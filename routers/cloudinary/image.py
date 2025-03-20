from fastapi import APIRouter, UploadFile
from libs.cloudinary import upload_image
from fastapi import Depends
from typing import Dict
from services.user_service import get_current_user

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/upload")
async def handle_upload(
    image: UploadFile, current_user: Dict = Depends(get_current_user)
):
    url = await upload_image(image)
    return {"data": {"url": url}}
