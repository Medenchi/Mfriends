from sqlite3 import Connection

from backend.app.api.deps import current_user_id
from backend.app.api.schemas import ProfileUpdate
from backend.app.core.rate_limit import rate_limit
from backend.app.core.validation import ensure_safe_text
from backend.app.db.connection import get_db
from fastapi import APIRouter, Depends, Request

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me")
def me(user_id: int = Depends(current_user_id), db: Connection = Depends(get_db)):
    row = db.execute(
        """
        SELECT u.id, u.email, u.is_email_verified, p.*, t.score AS trust_score
        FROM users u
        JOIN profiles p ON p.user_id = u.id
        LEFT JOIN trust_scores t ON t.user_id = u.id
        WHERE u.id = ?
        """,
        (user_id,),
    ).fetchone()
    return dict(row)


@router.put("/me")
async def update_me(
    payload: ProfileUpdate,
    request: Request,
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    rate_limit(request, f"profile-update-{user_id}", limit=10, window_seconds=300)
    db.execute(
        """
        UPDATE profiles SET
          display_name = ?, bio = ?, city = ?, timezone = ?, buddy_goals = ?, interests = ?,
          updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """,
        (
            ensure_safe_text(payload.display_name, 48),
            ensure_safe_text(payload.bio, 600),
            ensure_safe_text(payload.city, 80),
            ensure_safe_text(payload.timezone, 64),
            ensure_safe_text(payload.buddy_goals, 300),
            ensure_safe_text(payload.interests, 300),
            user_id,
        ),
    )
    db.commit()
    return {"status": "updated"}


@router.get("/discover")
def discover(
    q: str = "",
    city: str = "",
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    query = f"%{q.lower()}%"
    rows = db.execute(
        """
        SELECT p.user_id, p.display_name, p.bio, p.city, p.buddy_goals, p.interests,
               p.online_status, t.score AS trust_score
        FROM profiles p
        LEFT JOIN trust_scores t ON t.user_id = p.user_id
        WHERE p.user_id != ?
          AND (? = '' OR LOWER(p.city) = LOWER(?))
          AND (? = '%%' OR LOWER(p.display_name || ' ' || p.bio || ' ' || p.interests) LIKE ?)
        ORDER BY t.score DESC, p.updated_at DESC
        LIMIT 50
        """,
        (user_id, city, city, query, query),
    ).fetchall()
    return {"people": [dict(row) for row in rows]}
