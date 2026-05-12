from sqlite3 import Connection

from backend.app.api.deps import current_admin_id, current_user_id
from backend.app.api.schemas import AdminDecision, BlockCreate, ReportCreate
from backend.app.core.rate_limit import rate_limit
from backend.app.core.validation import ensure_safe_text
from backend.app.db.connection import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.post("/reports")
def create_report(
    payload: ReportCreate,
    request: Request,
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    rate_limit(request, f"report-{user_id}", limit=10, window_seconds=3600)
    cursor = db.execute(
        """
        INSERT INTO reports (reporter_id, reported_user_id, message_id, reason, details, priority)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            payload.reported_user_id,
            payload.message_id,
            ensure_safe_text(payload.reason, 80),
            ensure_safe_text(payload.details, 1000),
            "high" if payload.message_id else "normal",
        ),
    )
    db.commit()
    return {"id": int(cursor.lastrowid), "status": "open"}


@router.post("/blocks")
def block_user(
    payload: BlockCreate,
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    if payload.blocked_user_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block yourself")
    db.execute(
        """
        INSERT INTO blocks (blocker_id, blocked_user_id, reason)
        VALUES (?, ?, ?)
        ON CONFLICT(blocker_id, blocked_user_id) DO UPDATE SET reason = excluded.reason
        """,
        (user_id, payload.blocked_user_id, ensure_safe_text(payload.reason, 240)),
    )
    db.execute(
        """
        UPDATE friendships SET status = 'blocked', updated_at = CURRENT_TIMESTAMP
        WHERE (requester_id = ? AND addressee_id = ?) OR (requester_id = ? AND addressee_id = ?)
        """,
        (user_id, payload.blocked_user_id, payload.blocked_user_id, user_id),
    )
    db.commit()
    return {"status": "blocked"}


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
    blocks = db.execute("SELECT COUNT(*) AS count FROM blocks WHERE blocker_id = ?", (user_id,)).fetchone()
    return {
        "trust_score": dict(trust) if trust else None,
        "recent": [dict(row) for row in recent],
        "blocks": blocks["count"] if blocks else 0,
        "warnings": [
            "Never share exact address, passwords, seed phrases or payment codes.",
            "Rewards are only for gaming help, tutoring, coaching and shared tasks.",
            "Meet offline only in public places and tell a trusted person.",
        ],
    }


@router.get("/admin/queue")
def moderation_queue(
    _admin_id: int = Depends(current_admin_id),
    db: Connection = Depends(get_db),
):
    reports = db.execute(
        """
        SELECT r.*, reporter.email AS reporter_email, reported.email AS reported_email
        FROM reports r
        LEFT JOIN users reporter ON reporter.id = r.reporter_id
        LEFT JOIN users reported ON reported.id = r.reported_user_id
        WHERE r.status IN ('open', 'reviewing')
        ORDER BY CASE r.priority WHEN 'high' THEN 0 ELSE 1 END, r.created_at ASC
        LIMIT 100
        """
    ).fetchall()
    logs = db.execute(
        """
        SELECT ml.*, u.email FROM moderation_logs ml
        LEFT JOIN users u ON u.id = ml.user_id
        ORDER BY ml.created_at DESC
        LIMIT 100
        """
    ).fetchall()
    verifications = db.execute(
        """
        SELECT vs.*, u.email, p.display_name FROM verification_states vs
        JOIN users u ON u.id = vs.user_id
        JOIN profiles p ON p.user_id = vs.user_id
        WHERE vs.status IN ('pending_upload', 'manual_review')
        ORDER BY vs.created_at ASC
        LIMIT 100
        """
    ).fetchall()
    suspicious = db.execute(
        """
        SELECT u.id, u.email, p.display_name, t.* FROM trust_scores t
        JOIN users u ON u.id = t.user_id
        JOIN profiles p ON p.user_id = t.user_id
        WHERE t.score < 45 OR t.scam_signals > 0 OR t.spam_signals > 2 OR t.harassment_signals > 0
        ORDER BY t.score ASC
        LIMIT 100
        """
    ).fetchall()
    return {
        "reports": [dict(row) for row in reports],
        "ai_moderation_logs": [dict(row) for row in logs],
        "verification_review": [dict(row) for row in verifications],
        "suspicious_users": [dict(row) for row in suspicious],
    }


@router.patch("/admin/reports/{report_id}")
def update_report(
    report_id: int,
    payload: AdminDecision,
    _admin_id: int = Depends(current_admin_id),
    db: Connection = Depends(get_db),
):
    db.execute(
        "UPDATE reports SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (payload.status, report_id),
    )
    db.commit()
    return {"status": payload.status}


@router.get("/admin/analytics")
def analytics(_admin_id: int = Depends(current_admin_id), db: Connection = Depends(get_db)):
    users = db.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    verified = db.execute("SELECT COUNT(*) AS count FROM users WHERE is_email_verified = 1").fetchone()
    requests = db.execute("SELECT COUNT(*) AS count FROM requests").fetchone()
    messages = db.execute("SELECT COUNT(*) AS count FROM messages").fetchone()
    reports = db.execute("SELECT status, COUNT(*) AS count FROM reports GROUP BY status").fetchall()
    return {
        "users": users["count"],
        "verified_users": verified["count"],
        "requests": requests["count"],
        "messages": messages["count"],
        "reports_by_status": [dict(row) for row in reports],
    }
