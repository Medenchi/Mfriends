from sqlite3 import Connection

from backend.app.api.deps import current_user_id
from backend.app.api.schemas import MessageCreate
from backend.app.core.rate_limit import rate_limit
from backend.app.core.validation import ensure_safe_text
from backend.app.db.connection import get_db
from backend.app.services.moderation import log_moderation, moderate_text
from fastapi import APIRouter, Depends, HTTPException, Request, status

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("")
def list_chats(user_id: int = Depends(current_user_id), db: Connection = Depends(get_db)):
    rows = db.execute(
        """
        SELECT c.id, c.chat_type, c.title, c.created_at,
               GROUP_CONCAT(p.display_name, ', ') AS members
        FROM chats c
        JOIN chat_members cm ON cm.chat_id = c.id
        JOIN chat_members all_members ON all_members.chat_id = c.id
        JOIN profiles p ON p.user_id = all_members.user_id
        WHERE cm.user_id = ?
        GROUP BY c.id
        ORDER BY c.created_at DESC
        """,
        (user_id,),
    ).fetchall()
    return {"chats": [dict(row) for row in rows]}


@router.get("/{chat_id}/messages")
def list_messages(
    chat_id: int,
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    member = db.execute(
        "SELECT 1 FROM chat_members WHERE chat_id = ? AND user_id = ?",
        (chat_id, user_id),
    ).fetchone()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    rows = db.execute(
        """
        SELECT m.id, m.sender_id, p.display_name AS sender_name, m.body, m.attachment_url,
               m.voice_placeholder, m.moderation_status, m.created_at
        FROM messages m
        JOIN profiles p ON p.user_id = m.sender_id
        WHERE m.chat_id = ?
        ORDER BY m.created_at DESC
        LIMIT 100
        """,
        (chat_id,),
    ).fetchall()
    return {"messages": [dict(row) for row in reversed(rows)]}


@router.post("/{chat_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    chat_id: int,
    payload: MessageCreate,
    request: Request,
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    rate_limit(request, f"message-{user_id}", limit=60, window_seconds=60)
    if chat_id != payload.chat_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chat mismatch")
    member = db.execute(
        "SELECT 1 FROM chat_members WHERE chat_id = ? AND user_id = ?",
        (chat_id, user_id),
    ).fetchone()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    blocked = db.execute(
        """
        SELECT 1 FROM chat_members cm
        JOIN blocks b ON (b.blocked_user_id = cm.user_id AND b.blocker_id = ?)
                     OR (b.blocker_id = cm.user_id AND b.blocked_user_id = ?)
        WHERE cm.chat_id = ?
        """,
        (user_id, user_id, chat_id),
    ).fetchone()
    if blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat is blocked by safety controls")
    body = ensure_safe_text(payload.body, 2000)
    decision = await moderate_text(body)
    cursor = db.execute(
        """
        INSERT INTO messages (chat_id, sender_id, body, attachment_url, voice_placeholder, moderation_status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (chat_id, user_id, body, payload.attachment_url, int(payload.voice_placeholder), decision.decision),
    )
    message_id = int(cursor.lastrowid)
    log_moderation(db, user_id, "message", message_id, decision)
    return {"id": message_id, "moderation": decision.decision}
