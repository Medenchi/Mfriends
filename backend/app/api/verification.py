from datetime import UTC, datetime, timedelta
from random import SystemRandom
from sqlite3 import Connection

from backend.app.api.deps import current_user_id
from backend.app.api.schemas import VerificationStart
from backend.app.db.connection import get_db
from backend.app.services.uploads import save_upload
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

router = APIRouter(prefix="/verification", tags=["verification"])


def purge_expired_verification_data(db: Connection) -> int:
    rows = db.execute(
        "SELECT id FROM verification_states WHERE expires_at IS NOT NULL AND expires_at < ?",
        (datetime.now(UTC).isoformat(),),
    ).fetchall()
    db.execute(
        """
        UPDATE verification_states
        SET file_url = NULL, code = NULL, status = 'expired', updated_at = CURRENT_TIMESTAMP
        WHERE expires_at IS NOT NULL AND expires_at < ? AND status != 'approved'
        """,
        (datetime.now(UTC).isoformat(),),
    )
    db.commit()
    return len(rows)


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
        "auto_delete_after": expires_at.isoformat(),
    }


@router.post("/{verification_id}/upload")
async def upload_verification_file(
    verification_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    saved = await save_upload(db, user_id, file)
    expires_at = datetime.now(UTC) + timedelta(hours=24)
    db.execute(
        """
        UPDATE verification_states
        SET file_url = ?, status = 'manual_review', expires_at = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        """,
        (saved["url"], expires_at.isoformat(), verification_id, user_id),
    )
    db.commit()
    background_tasks.add_task(purge_expired_verification_data, db)
    return {"status": "manual_review", "file": saved, "auto_delete_after": expires_at.isoformat()}


@router.get("/states")
def list_states(user_id: int = Depends(current_user_id), db: Connection = Depends(get_db)):
    rows = db.execute(
        """
        SELECT id, verification_type, status, file_url, expires_at, created_at, updated_at
        FROM verification_states
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (user_id,),
    ).fetchall()
    return {"states": [dict(row) for row in rows]}
