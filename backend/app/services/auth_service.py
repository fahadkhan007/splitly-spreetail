# app/services/auth_service.py
#
# Business logic for the authentication flow.
# This layer orchestrates: DB queries, password checks, token creation, and emails.
# It raises HTTPException for any error — the router just calls these functions.

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.email import send_verification_email
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_email_verification_token,
    decode_token,
)
from app.models.user import User
from app.repositories.user_repo import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    mark_user_verified,
)


async def register_user(
    db: AsyncSession,
    email: str,
    display_name: str,
    password: str,
    invite_token: str | None = None,
) -> User:
    """
    Registers a new user.

    Steps:
      1. Check the email isn't already taken
      2. Hash the password
      3. Save the user to the database (is_verified=False)
      4. Send a verification email with a link
      5. If an invite_token was provided, add the user to that group automatically
    """
    # Step 1: Reject duplicate emails
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    # Step 2: Hash the password — we never store plain text
    hashed = hash_password(password)

    # Step 3: Save the user
    user = await create_user(db, email=email, display_name=display_name, password_hash=hashed)

    # Step 4: Send verification email
    token = create_email_verification_token(email)
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    send_verification_email(email, verification_link)

    # Step 5: If the user registered via a group invite link, add them to the group
    if invite_token:
        from app.services.invitation_service import accept_invite_on_registration
        await accept_invite_on_registration(db, token=invite_token, new_user=user)

    return user


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, str, str]:
    """
    Logs in a user with email + password.

    Returns: (user, access_token, refresh_token)

    Note: We return the same error message for "wrong email" and "wrong password"
    intentionally — this prevents attackers from guessing which emails exist.
    """
    user = await get_user_by_email(db, email)

    # Check user exists and has a password (PENDING users have no password)
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check the password matches
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create both tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)

    return user, access_token, refresh_token


async def verify_user_email(db: AsyncSession, token: str) -> User:
    """
    Verifies a user's email address using the token from the verification link.

    The token contains the user's email and expires after 24 hours.
    After this, the user's is_verified flag is set to True.
    """
    payload = decode_token(token)

    # Token must be valid and must be the right type
    if not payload or payload.get("type") != "email_verify":
        raise HTTPException(
            status_code=400,
            detail="This verification link is invalid or has expired. Please request a new one."
        )

    email = payload["sub"]
    user = await get_user_by_email(db, email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # If already verified, just return success (idempotent)
    if user.is_verified:
        return user

    # Mark as verified
    user = await mark_user_verified(db, user)
    return user


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> tuple[User, str]:
    """
    Uses a refresh token (from the HttpOnly cookie) to issue a new access token.

    Returns: (user, new_access_token)
    """
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await get_user_by_id(db, payload["sub"])

    if not user:
        raise HTTPException(status_code=401, detail="User account not found")

    new_access_token = create_access_token(user.id, user.email)
    return user, new_access_token
