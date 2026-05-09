from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

SAFE_UPLOAD_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "audio/webm": ".webm",
    "audio/mpeg": ".mp3",
}


def ensure_safe_text(value: str, max_length: int = 2000) -> str:
    cleaned = " ".join(value.strip().split())
    if len(cleaned) > max_length:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Text too long")
    return cleaned


def upload_filename(file: UploadFile) -> str:
    if file.content_type not in SAFE_UPLOAD_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported upload type",
        )
    return f"{uuid4().hex}{SAFE_UPLOAD_TYPES[file.content_type]}"


def safe_upload_path(upload_dir: Path, filename: str) -> Path:
    path = upload_dir / filename
    resolved_dir = upload_dir.resolve()
    resolved_path = path.resolve()
    if resolved_dir not in resolved_path.parents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsafe upload path")
    return resolved_path
