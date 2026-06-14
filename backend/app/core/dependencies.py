# app/core/dependencies.py
#
# FastAPI "dependencies" are functions that run before a route handler.
# They handle things like: "is this user logged in?", "is this user an admin?"
#
# Usage in a router:
#   @router.get("/something")
#   async def do_something(current_user = Depends(get_current_user)):
#       ...

from fastapi import Depends, HTTPException, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserStatus

# This tells FastAPI to look for a Bearer token in the Authorization header
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Reads the access token from the Authorization header, decodes it,
    and returns the logged-in user.

    Raises 401 if the token is missing, invalid, or expired.
    Raises 403 if the account is not ACTIVE (e.g. it's a PENDING member).
    """
    from app.repositories.user_repo import get_user_by_id  # imported here to avoid circular import

    token = credentials.credentials
    payload = decode_token(token)

    # Token must exist and must be an access token (not a refresh or verify token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    user_id = payload.get("sub")
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User account not found")

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="This account is not active")

    return user


async def require_verified_email(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Use this instead of get_current_user for routes that require the user
    to have verified their email first (e.g. adding expenses, inviting others).

    Raises 403 if the user's email is not yet verified.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email address before performing this action.",
        )
    return current_user
