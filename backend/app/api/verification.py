from datetime import UTC, datetime, timedelta
from random import SystemRandom
from sqlite3 import Connection

from backend.app.api.deps import current_user_id
from backend.app.api.schemas import VerificationStart
from backend.app.db.connection import get_db
from backend.app.services.uploads import save_upload
from fastapi import APIRouter, Depends, File, UploadFile

router = APIRouter(prefix="/verification", tags=["verification"])


@router.post("/start")
def start_verification(
    payload: VerificationStart,
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    code = f"{SystemRandom().randint(100000, 999999)}"
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    cursor = db.execute(
        """
        INSERT INTO verification_states (user_id, verification_type, status, code, expires_at)
        VALUES (?, ?, 'pending_upload', ?, ?)
        """,
        (user_id, payload.verification_type, code, expires_at.isoformat()),
    )
    db.commit()
    return {
        "id": int(cursor.lastrowid),
        "status": "pending_upload",
        "voice_code": code if payload.verification_type == "voice_code" else None,
        "liveness_prompt": "Turn head left, blink twice, then say the shown code.",
    }


@router.post("/{verification_id}/upload")
async def upload_verification_file(
    verification_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    saved = await save_upload(db, user_id, file)
    db.execute(
        """
        UPDATE verification_states
        SET file_url = ?, status = 'manual_review', updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        """,
        (saved["url"], verification_id, user_id),
    )
    db.commit()
    return {"status": "manual_review", "file": saved}
