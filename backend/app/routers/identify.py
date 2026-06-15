from fastapi import APIRouter, File, UploadFile

from app.schemas import IdentificationResult
from app.services.identify import identify_service
from app.services.upload_validator import (
    validate_audio_upload,
    validate_image_upload,
    validate_video_upload,
)

router = APIRouter(prefix="/identify", tags=["identify"])


@router.post("/image", response_model=IdentificationResult)
async def identify_image(file: UploadFile = File(...)) -> IdentificationResult:
    content = await file.read()
    validate_image_upload(content, file.filename)
    return identify_service.identify_image(content)


@router.post("/audio", response_model=IdentificationResult)
async def identify_audio(file: UploadFile = File(...)) -> IdentificationResult:
    content = await file.read()
    validate_audio_upload(content, file.filename)
    return identify_service.identify_audio(content, filename=file.filename or "")


@router.post("/video", response_model=IdentificationResult)
async def identify_video(file: UploadFile = File(...)) -> IdentificationResult:
    content = await file.read()
    validate_video_upload(content, file.filename)
    return identify_service.identify_video()
