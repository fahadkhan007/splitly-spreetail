# app/core/security.py
#
# All password and JWT (token) functions live here.
# Nothing else — no DB access, no HTTP, just pure utilities.

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import jwt, JWTError

from app.config import settings

# ── ALGORITHM ────────────────────────────────────────────────────
# HS256 = HMAC + SHA-256. Simple and widely supported.
ALGORITHM = "HS256"


# ── PASSWORD FUNCTIONS ───────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Hashes a plain-text password using bcrypt.
    The result is a string that is safe to store in the database.
    """
    hashed_bytes = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks whether a plain-text password matches a stored bcrypt hash.
    Returns True if they match, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ── TOKEN CREATION ───────────────────────────────────────────────

def create_access_token(user_id: UUID, email: str) -> str:
    """
    Creates a short-lived JWT access token.
    This is sent in the Authorization header on every protected request.
    Expires in ACCESS_TOKEN_EXPIRE_MINUTES (default: 15 minutes).
    """
    payload = {
        "sub": str(user_id),    # "sub" = subject — who this token belongs to
        "email": email,
        "type": "access",       # We check this type when validating
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """
    Creates a long-lived JWT refresh token.
    This is stored in an HttpOnly cookie (browser JS cannot read it).
    Used to get a new access token when the old one expires.
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
    Creates a token embedded in the email verification link.
    When the user clicks the link, we decode this token to find their email.
    Expires in 24 hours.
    """
    payload = {
        "sub": email,
        "type": "email_verify",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


# ── TOKEN DECODING ───────────────────────────────────────────────

def decode_token(token: str) -> dict | None:
    """
    Decodes a JWT token and returns the payload as a dictionary.
    Returns None if the token is invalid, expired, or tampered with.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
