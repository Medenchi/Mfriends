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
        SELECT u.id, u.id AS user_id, u.email, u.is_email_verified, u.role, p.*, t.score AS trust_score
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
          display_name = ?, username = ?, bio = ?, city = ?, district = ?, timezone = ?,
          buddy_goals = ?, interests = ?, games = ?, hobbies = ?, online_offline_preference = ?,
          friendship_preference = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """,
        (
            ensure_safe_text(payload.display_name, 48),
            ensure_safe_text(payload.username or payload.display_name.lower().replace(" ", "-"), 32),
            ensure_safe_text(payload.bio, 600),
            ensure_safe_text(payload.city, 80),
            ensure_safe_text(payload.district, 80),
            ensure_safe_text(payload.timezone, 64),
            ensure_safe_text(payload.buddy_goals, 300),
            ensure_safe_text(payload.interests, 300),
            ensure_safe_text(payload.games, 300),
            ensure_safe_text(payload.hobbies, 300),
            payload.online_offline_preference,
            payload.friendship_preference,
            user_id,
        ),
    )
    db.commit()
    return {"status": "updated"}


@router.get("/discover")
def discover(
    q: str = "",
    interests: str = "",
    games: str = "",
    city: str = "",
    district: str = "",
    mode: str = "",
    verified_only: bool = False,
    category: str = "",
    user_id: int = Depends(current_user_id),
    db: Connection = Depends(get_db),
):
    query = f"%{q.lower()}%"
    interests_query = f"%{interests.lower()}%"
    games_query = f"%{games.lower()}%"
    category_query = f"%{category.lower()}%"
    rows = db.execute(
        """
        SELECT p.user_id, p.display_name, p.username, p.bio, p.city, p.district, p.buddy_goals,
               p.interests, p.games, p.hobbies, p.online_offline_preference, p.friendship_preference,
               p.online_status, p.avatar_url, p.verification_badge, u.is_email_verified,
               t.score AS trust_score
        FROM profiles p
        JOIN users u ON u.id = p.user_id
        LEFT JOIN trust_scores t ON t.user_id = p.user_id
        WHERE p.user_id != ?
          AND u.is_active = 1
          AND NOT EXISTS (
            SELECT 1 FROM blocks b
            WHERE (b.blocker_id = ? AND b.blocked_user_id = p.user_id)
               OR (b.blocker_id = p.user_id AND b.blocked_user_id = ?)
          )
          AND (? = '' OR LOWER(p.city) = LOWER(?))
          AND (? = '' OR LOWER(p.district) = LOWER(?))
          AND (? = '' OR p.online_offline_preference IN (?, 'both'))
          AND (? = 0 OR u.is_email_verified = 1 OR p.verification_badge != 'none')
          AND (? = '%%' OR LOWER(p.display_name || ' ' || p.username || ' ' || p.bio || ' ' || p.interests || ' ' || p.games || ' ' || p.hobbies || ' ' || p.buddy_goals) LIKE ?)
          AND (? = '%%' OR LOWER(p.interests || ' ' || p.hobbies || ' ' || p.buddy_goals) LIKE ?)
          AND (? = '%%' OR LOWER(p.games || ' ' || p.buddy_goals) LIKE ?)
          AND (? = '%%' OR LOWER(p.buddy_goals || ' ' || p.interests || ' ' || p.hobbies) LIKE ?)
        ORDER BY COALESCE(t.score, 50) DESC, p.updated_at DESC
        LIMIT 50
        """,
        (
            user_id,
            user_id,
            user_id,
            city,
            city,
            district,
            district,
            mode,
            mode,
            int(verified_only),
            query,
            query,
            interests_query,
            interests_query,
            games_query,
            games_query,
            category_query,
            category_query,
        ),
    ).fetchall()
    return {"people": [dict(row) for row in rows]}
