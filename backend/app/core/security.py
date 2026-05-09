from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

import bcrypt
from backend.app.core.config import get_settings
from jose import JWTError, jwt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "type": "access", "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": subject, "type": "refresh", "jti": token_urlsafe(16), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str = "access") -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None


def make_random_token() -> str:
    return token_urlsafe(32)
