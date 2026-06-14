# app/config.py
#
# This file reads all environment variables from the .env file
# and makes them available throughout the application as `settings`.
#
# Usage anywhere in the app:
#   from app.config import settings
#   print(settings.SECRET_KEY)

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str           # Sync URL for Alembic migrations
    ASYNC_DATABASE_URL: str     # Async URL for FastAPI runtime

    # JWT tokens
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email
    RESEND_API_KEY: str = ""

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    FRANKFURTER_BASE_URL: str = "https://api.frankfurter.app"

    class Config:
        # Tell pydantic-settings to read from the .env file
        env_file = ".env"


# Single shared instance — import this everywhere
settings = Settings()
