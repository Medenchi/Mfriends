from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from sqlite3 import Connection

import aiosmtplib
from backend.app.core.config import get_settings
from backend.app.core.security import make_random_token


def create_email_token(db: Connection, user_id: int, token_type: str, minutes: int = 30) -> str:
    token = make_random_token()
    expires_at = datetime.now(UTC) + timedelta(minutes=minutes)
    db.execute(
        """
        INSERT INTO email_tokens (user_id, token, token_type, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, token, token_type, expires_at.isoformat()),
    )
    db.commit()
    return token


def verification_email_html(url: str) -> str:
    return f"""
    <div style="background:#101010;color:#F3F3F3;font-family:Arial,sans-serif;padding:24px">
      <h1 style="line-height:1">Verify your MFriends email</h1>
      <p style="color:#949494">Confirm this address to unlock requests, chat and trust features.</p>
      <a href="{url}" style="display:inline-block;background:#333;color:#fff;padding:12px 16px;border-radius:8px;text-decoration:none">Verify email</a>
    </div>
    """


def reset_email_html(url: str) -> str:
    return f"""
    <div style="background:#101010;color:#F3F3F3;font-family:Arial,sans-serif;padding:24px">
      <h1 style="line-height:1">Reset your MFriends password</h1>
      <p style="color:#949494">This link expires soon. Ignore it if you did not request a reset.</p>
      <a href="{url}" style="display:inline-block;background:#333;color:#fff;padding:12px 16px;border-radius:8px;text-decoration:none">Reset password</a>
    </div>
    """


async def send_email(to_email: str, subject: str, html: str) -> None:
    settings = get_settings()
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content("Open this message in an HTML email client.")
    message.add_alternative(html, subtype="html")
    if settings.app_env == "development" and settings.smtp_host == "localhost":
        return
    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username or None,
        password=settings.smtp_password or None,
        start_tls=settings.smtp_tls,
    )


async def send_verification_email(db: Connection, user_id: int, email: str) -> None:
    settings = get_settings()
    token = create_email_token(db, user_id, "verify_email")
    url = f"{settings.api_base_url}/auth/verify-email?token={token}"
    await send_email(email, "Verify your MFriends email", verification_email_html(url))


async def send_password_reset_email(db: Connection, user_id: int, email: str) -> None:
    settings = get_settings()
    token = create_email_token(db, user_id, "password_reset", minutes=20)
    url = f"{settings.app_base_url}/reset-password.html?token={token}"
    await send_email(email, "Reset your MFriends password", reset_email_html(url))
