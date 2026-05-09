from sqlite3 import Connection

from backend.app.core.config import get_settings
from backend.app.core.validation import safe_upload_path, upload_filename
from fastapi import HTTPException, UploadFile, status


async def save_upload(db: Connection, owner_id: int, file: UploadFile) -> dict[str, str | int]:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    filename = upload_filename(file)
    path = safe_upload_path(settings.upload_dir, filename)
    total = 0
    with path.open("wb") as output:
        while chunk := await file.read(1024 * 512):
            total += len(chunk)
            if total > settings.max_upload_size_bytes:
                path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File is too large",
                )
            output.write(chunk)
    public_url = f"/uploads/{filename}"
    db.execute(
        """
        INSERT INTO upload_files
          (owner_id, filename, original_name, content_type, size_bytes, storage_path, public_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (owner_id, filename, file.filename or filename, file.content_type or "", total, str(path), public_url),
    )
    db.commit()
    return {"filename": filename, "url": public_url, "size_bytes": total}
