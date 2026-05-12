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
REWARD_ALLOWED_CATEGORIES = {"gaming", "coding", "studying", "tutoring", "coaching", "task"}
REWARD_FORBIDDEN_TERMS = {
    "dating",
    "date",
    "escort",
    "adult",
    "companionship",
    "girlfriend",
    "boyfriend",
    "romance",
    "sex",
}


def ensure_safe_text(value: str, max_length: int = 2000) -> str:
    cleaned = " ".join(value.strip().split())
    if len(cleaned) > max_length:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Text too long")
    return cleaned


def validate_reward(reward: str, category: str, text: str) -> str:
    cleaned = ensure_safe_text(reward, 120)
    if not cleaned:
        return ""
    lower_context = f"{category} {text} {cleaned}".lower()
    if category.lower() not in REWARD_ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rewards are only allowed for gaming help, tutoring, coaching and shared tasks",
        )
    if any(term in lower_context for term in REWARD_FORBIDDEN_TERMS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rewards for dating, adult services or paid companionship are forbidden",
        )
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
