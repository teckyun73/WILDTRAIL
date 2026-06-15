from io import BytesIO
from pathlib import Path

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from app.config import get_settings

settings = get_settings()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}

IMAGE_MAGIC = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"RIFF": "webp",
}


def _max_bytes(mb: float) -> int:
    return int(mb * 1024 * 1024)


def _extension(filename: str | None) -> str:
    if not filename:
        return ""
    return Path(filename).suffix.lower()


def _check_size(content: bytes, max_mb: float, label: str) -> None:
    limit = _max_bytes(max_mb)
    if len(content) == 0:
        raise HTTPException(status_code=400, detail=f"{label} 파일이 비어 있습니다.")
    if len(content) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"{label} 파일 크기는 {max_mb}MB 이하여야 합니다. (현재: {len(content) / 1024 / 1024:.1f}MB)",
        )


def _check_extension(filename: str | None, allowed: set[str], label: str) -> None:
    ext = _extension(filename)
    if not ext:
        raise HTTPException(
            status_code=415,
            detail=f"{label} 파일 확장자를 확인할 수 없습니다. 허용: {', '.join(sorted(allowed))}",
        )
    if ext not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 {label} 형식입니다. 허용: {', '.join(sorted(allowed))}",
        )


def _sniff_image_type(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def validate_image_upload(content: bytes, filename: str | None) -> None:
    _check_size(content, settings.max_image_mb, "이미지")
    _check_extension(filename, IMAGE_EXTENSIONS, "이미지")

    if _sniff_image_type(content) is None:
        raise HTTPException(
            status_code=415,
            detail="이미지 파일 형식을 확인할 수 없습니다. JPG, PNG, WEBP만 지원합니다.",
        )

    try:
        with Image.open(BytesIO(content)) as img:
            img.verify()
        with Image.open(BytesIO(content)) as img:
            img.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="손상되었거나 읽을 수 없는 이미지 파일입니다.",
        ) from exc


def validate_audio_upload(content: bytes, filename: str | None) -> None:
    _check_size(content, settings.max_audio_mb, "오디오")
    _check_extension(filename, AUDIO_EXTENSIONS, "오디오")


def validate_video_upload(content: bytes, filename: str | None) -> None:
    _check_size(content, settings.max_video_mb, "영상")
    _check_extension(filename, VIDEO_EXTENSIONS, "영상")
