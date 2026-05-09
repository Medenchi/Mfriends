from sqlite3 import Connection

from backend.app.core.security import decode_token
from backend.app.db.connection import get_db
from fastapi import Depends, Header, HTTPException, status


def current_user_id(
    authorization: str | None = Header(default=None),
    db: Connection = Depends(get_db),
) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    subject = decode_token(authorization.split(" ", maxsplit=1)[1])
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.execute("SELECT id, is_active FROM users WHERE id = ?", (int(subject),)).fetchone()
    if not user or not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return int(user["id"])
