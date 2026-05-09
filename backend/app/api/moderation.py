from sqlite3 import Connection

from backend.app.api.deps import current_user_id
from backend.app.api.schemas import ReportCreate
from backend.app.core.validation import ensure_safe_text
from backend.app.db.connection import get_db
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.post("/reports")
def create_report(
    payload: ReportCreate,
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    cursor = db.execute(
        """
        INSERT INTO reports (reporter_id, reported_user_id, message_id, reason, details)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            payload.reported_user_id,
            payload.message_id,
            ensure_safe_text(payload.reason, 80),
            ensure_safe_text(payload.details, 1000),
        ),
    )
    db.commit()
    return {"id": int(cursor.lastrowid), "status": "open"}


@router.get("/safety-summary")
def safety_summary(user_id: int = Depends(current_user_id), db: Connection = Depends(get_db)):
    trust = db.execute("SELECT * FROM trust_scores WHERE user_id = ?", (user_id,)).fetchone()
    recent = db.execute(
        """
        SELECT decision, content_type, created_at FROM moderation_logs
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (user_id,),
    ).fetchall()
    return {"trust_score": dict(trust) if trust else None, "recent": [dict(row) for row in recent]}
