# app/routers/auth.py
#
# HTTP routes for authentication.
# Each route is thin — it just calls the service and returns a response.
# All business logic is in services/auth_service.py.
#
# Routes:
#   POST /auth/register      — create account + send verification email
#   GET  /auth/verify-email  — confirm email via link token
#   POST /auth/login         — get access token + set refresh token cookie
#   POST /auth/refresh       — swap refresh token cookie for new access token

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest, TokenResponse
from app.schemas.user import UserOut
from app.services.auth_service import (
    login_user,
    refresh_access_token,
    register_user,
    verify_user_email,
)

router = APIRouter()


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Creates a new user account.
    A verification email is sent automatically after registration.
    The user can log in immediately but some features require email verification.
    """
    await register_user(db, email=body.email, display_name=body.display_name, password=body.password)
    return {"message": "Account created successfully. Please check your email to verify your account."}


@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verifies the user's email address.
    Called when the user clicks the link in their verification email.
    The token comes from the URL query parameter: /auth/verify-email?token=...
    """
    await verify_user_email(db, token=token)
    return {"message": "Email verified successfully. You can now use all features."}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Logs in a user with email and password.

    Returns:
    - access_token in the response body (frontend stores this in memory)
    - refresh_token as an HttpOnly cookie (browser stores this automatically)
    """
    user, access_token, refresh_token = await login_user(db, email=body.email, password=body.password)

    # Set the refresh token as an HttpOnly cookie.
    # HttpOnly = JavaScript in the browser CANNOT read this cookie.
    # This protects against XSS attacks stealing the refresh token.
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # seconds
        samesite="lax",
        secure=False,  # Change to True in production (requires HTTPS)
    )

    return TokenResponse(
        access_token=access_token,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str = Cookie(default=None),  # Read from the HttpOnly cookie
):
    """
    Issues a new access token using the refresh token stored in the cookie.
    Call this when the access token expires (after 15 minutes).
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found. Please log in again.")

    user, new_access_token = await refresh_access_token(db, refresh_token=refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        user=UserOut.model_validate(user),
    )
