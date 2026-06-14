# app/schemas/auth.py
#
# Request and response shapes for the authentication endpoints.

from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    """Body for POST /auth/register"""
    email: EmailStr
    display_name: str
    password: str

    @field_validator("password")
    def password_long_enough(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value

    @field_validator("display_name")
    def display_name_not_blank(cls, value):
        if not value.strip():
            raise ValueError("Display name cannot be empty")
        return value.strip()


class LoginRequest(BaseModel):
    """Body for POST /auth/login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Returned by /auth/login and /auth/refresh.
    The access token goes in the Authorization header for future requests.
    The refresh token is sent as an HttpOnly cookie (not in this response body).
    """
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageResponse(BaseModel):
    """Simple message-only response (e.g. for register and verify-email)."""
    message: str
