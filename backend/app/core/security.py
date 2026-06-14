# app/core/security.py
#
# All password and JWT (token) functions live here.
# Nothing else — no DB access, no HTTP, just import bcrypt as _bcrypt

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt as _bcrypt
from jose import jwt, JWTError

from app.config import settings

# ── PASSWORD HASHING ─────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Hashes a plain-text password. Safe to store in the database."""
    salt = _bcrypt.gensalt()
    hashed = _bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Returns True if the plain password matches the stored hash."""
    return _bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ── ALGORITHM ────────────────────────────────────────────────────
ALGORITHM = "HS256"


# ── TOKEN CREATION ───────────────────────────────────────────────

def create_access_token(user_id: UUID, email: str) -> str:
    """
    Short-lived token sent in the Authorization header on every request.
    Expires in ACCESS_TOKEN_EXPIRE_MINUTES (default: 15 minutes).
    """
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """
    Long-lived token stored in an HttpOnly cookie.
    Used to get a new access token when the current one expires.
    Expires in REFRESH_TOKEN_EXPIRE_DAYS (default: 7 days).
    """
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_email_verification_token(email: str) -> str:
    """
    Token embedded in the email verification link. Expires in 24 hours.
    """
    payload = {
        "sub": email,
        "type": "email_verify",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_invite_token(group_id: str, invited_email: str) -> str:
    """
    Token embedded in group invitation links. Expires in 7 days.
    """
    payload = {
        "group_id": group_id,
        "invited_email": invited_email,
        "type": "group_invite",
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """
    Decodes a JWT. Returns the payload dict, or None if invalid/expired.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
