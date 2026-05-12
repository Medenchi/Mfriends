from sqlite3 import Connection

from backend.app.api.deps import current_user_id
from backend.app.api.schemas import RequestCreate
from backend.app.core.rate_limit import rate_limit
from backend.app.core.validation import ensure_safe_text, validate_reward
from backend.app.db.connection import get_db
from backend.app.services.moderation import log_moderation, moderate_text
from fastapi import APIRouter, Depends, HTTPException, Request, status

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("")
def list_requests(user_id: int = Depends(current_user_id), db: Connection = Depends(get_db)):
    rows = db.execute(
        """
        SELECT r.*, p.display_name AS sender_name
        FROM requests r
        JOIN profiles p ON p.user_id = r.sender_id
        WHERE r.receiver_id = ? OR r.sender_id = ? OR r.receiver_id IS NULL
        ORDER BY r.created_at DESC
        LIMIT 100
        """,
        (user_id, user_id),
    ).fetchall()
    return {"requests": [dict(row) for row in rows]}


@router.get("/public")
def public_requests(
    q: str = "",
    category: str = "",
    mode: str = "",
    tags: str = "",
    db: Connection = Depends(get_db),
):
    query = f"%{q.lower()}%"
    tag_query = f"%{tags.lower()}%"
    rows = db.execute(
        """
        SELECT r.*, p.display_name AS sender_name, p.city, p.district, t.score AS trust_score
        FROM requests r
        JOIN profiles p ON p.user_id = r.sender_id
        LEFT JOIN trust_scores t ON t.user_id = r.sender_id
        WHERE r.receiver_id IS NULL AND r.status = 'pending'
          AND (? = '' OR r.category = ?)
          AND (? = '' OR r.mode = ?)
          AND (? = '%%' OR LOWER(r.title || ' ' || r.description || ' ' || r.tags) LIKE ?)
          AND (? = '%%' OR LOWER(r.tags) LIKE ?)
        ORDER BY r.created_at DESC
        LIMIT 100
        """,
        (category, category, mode, mode, query, query, tag_query, tag_query),
    ).fetchall()
    return {"requests": [dict(row) for row in rows]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: RequestCreate,
    request: Request,
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    rate_limit(request, f"request-create-{user_id}", limit=20, window_seconds=3600)
    if payload.receiver_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot request yourself")
    if payload.receiver_id:
        blocked = db.execute(
            """
            SELECT 1 FROM blocks
            WHERE (blocker_id = ? AND blocked_user_id = ?) OR (blocker_id = ? AND blocked_user_id = ?)
            """,
            (user_id, payload.receiver_id, payload.receiver_id, user_id),
        ).fetchone()
        if blocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Request blocked by safety controls")
    reward = validate_reward(payload.reward, payload.category, payload.description)
    title = ensure_safe_text(payload.title or payload.request_type.title(), 80)
    description = ensure_safe_text(payload.description or payload.message, 800)
    message = ensure_safe_text(payload.message or description, 500)
    tags = ensure_safe_text(payload.tags, 240)
    decision = await moderate_text(f"{title}\n{description}\n{message}\n{tags}")
    cursor = db.execute(
        """
        INSERT INTO requests
          (sender_id, receiver_id, request_type, title, description, message, tags, category, mode, reward, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            payload.receiver_id,
            ensure_safe_text(payload.request_type, 32),
            title,
            description,
            message,
            tags,
            ensure_safe_text(payload.category, 40),
            payload.mode,
            reward,
            "pending" if decision.allowed else "blocked",
        ),
    )
    request_id = int(cursor.lastrowid)
    log_moderation(db, user_id, "request", request_id, decision)
    return {"id": request_id, "moderation": decision.decision}


@router.post("/{request_id}/{decision}")
def answer_request(
    request_id: int,
    decision: str,
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    if decision not in {"accepted", "declined"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid decision")
    row = db.execute(
        """
        SELECT * FROM requests
        WHERE id = ? AND (receiver_id = ? OR (receiver_id IS NULL AND sender_id != ?))
        """,
        (request_id, user_id, user_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    db.execute(
        "UPDATE requests SET status = ?, receiver_id = COALESCE(receiver_id, ?), updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (decision, user_id, request_id),
    )
    if decision == "accepted":
        db.execute(
            """
            INSERT OR IGNORE INTO friendships (requester_id, addressee_id, status)
            VALUES (?, ?, 'accepted')
            """,
            (row["sender_id"], user_id),
        )
        cursor = db.execute("INSERT INTO chats (chat_type, title) VALUES ('direct', NULL)")
        chat_id = int(cursor.lastrowid)
        db.executemany(
            "INSERT INTO chat_members (chat_id, user_id) VALUES (?, ?)",
            [(chat_id, row["sender_id"]), (chat_id, user_id)],
        )
    db.commit()
    return {"status": decision}
