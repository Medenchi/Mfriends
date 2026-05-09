from sqlite3 import Connection

from backend.app.api.deps import current_user_id
from backend.app.core.rate_limit import rate_limit
from backend.app.db.connection import get_db
from backend.app.services.uploads import save_upload
from fastapi import APIRouter, Depends, File, Request, UploadFile

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    rate_limit(request, f"upload-{user_id}", limit=20, window_seconds=3600)
    return await save_upload(db, user_id, file)
