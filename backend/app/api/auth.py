from datetime import UTC, datetime
from sqlite3 import Connection, IntegrityError

from backend.app.api.schemas import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
)
from backend.app.core.rate_limit import rate_limit
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from backend.app.db.connection import get_db
from backend.app.services.email import send_password_reset_email, send_verification_email
from fastapi import APIRouter, Depends, HTTPException, Request, status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, db: Connection = Depends(get_db)):
    rate_limit(request, "auth-register", limit=5, window_seconds=300)
    try:
        cursor = db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (payload.email.lower(), hash_password(payload.password)),
        )
        user_id = int(cursor.lastrowid)
        db.execute(
            """
            INSERT INTO profiles (user_id, display_name, buddy_goals)
            VALUES (?, ?, 'friendship, study buddy, gaming buddy, coding buddy')
            """,
            (user_id, payload.display_name.strip()),
        )
        db.execute("INSERT INTO trust_scores (user_id) VALUES (?)", (user_id,))
        db.commit()
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists") from exc
    await send_verification_email(db, user_id, payload.email.lower())
    return TokenResponse(
        access_token=create_access_token(str(user_id)),
        refresh_token=create_refresh_token(str(user_id)),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Connection = Depends(get_db)):
    rate_limit(request, "auth-login", limit=10, window_seconds=300)
    user = db.execute(
        "SELECT id, password_hash, is_active FROM users WHERE email = ?",
        (payload.email.lower(),),
    ).fetchone()
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return TokenResponse(
        access_token=create_access_token(str(user["id"])),
        refresh_token=create_refresh_token(str(user["id"])),
    )


@router.get("/verify-email")
def verify_email(token: str, db: Connection = Depends(get_db)):
    row = db.execute(
        """
        SELECT id, user_id, expires_at, used_at FROM email_tokens
        WHERE token = ? AND token_type = 'verify_email'
        """,
        (token,),
    ).fetchone()
    if not row or row["used_at"] or datetime.fromisoformat(row["expires_at"]) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    db.execute("UPDATE users SET is_email_verified = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (row["user_id"],))
    db.execute("UPDATE email_tokens SET used_at = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))
    db.commit()
    return {"status": "verified"}


@router.post("/password-reset/request")
async def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: Connection = Depends(get_db),
):
    rate_limit(request, "password-reset", limit=3, window_seconds=900)
    user = db.execute("SELECT id, email FROM users WHERE email = ?", (payload.email.lower(),)).fetchone()
    if user:
        await send_password_reset_email(db, int(user["id"]), str(user["email"]))
    return {"status": "if-account-exists-email-sent"}


@router.post("/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, db: Connection = Depends(get_db)):
    row = db.execute(
        """
        SELECT id, user_id, expires_at, used_at FROM email_tokens
        WHERE token = ? AND token_type = 'password_reset'
        """,
        (payload.token,),
    ).fetchone()
    if not row or row["used_at"] or datetime.fromisoformat(row["expires_at"]) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    db.execute(
        "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (hash_password(payload.password), row["user_id"]),
    )
    db.execute("UPDATE email_tokens SET used_at = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))
    db.commit()
    return {"status": "password-updated"}
