# app/config.py
#
# This file reads all environment variables from the .env file
# and makes them available throughout the application as `settings`.
#
# NOTE: ASYNC_DATABASE_URL is automatically derived from DATABASE_URL by
# replacing "postgresql://" with "postgresql+asyncpg://". You only ever
# need to set DATABASE_URL in your environment (e.g. Railway, .env).
#
# Usage anywhere in the app:
#   from app.config import settings
#   print(settings.SECRET_KEY)

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str               # Sync URL — set this in Railway/env
    ASYNC_DATABASE_URL: str = ""    # Auto-derived below; can be overridden

    # JWT tokens
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email
    RESEND_API_KEY: str = ""

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    FRANKFURTER_BASE_URL: str = "https://api.frankfurter.app"

    @model_validator(mode="after")
    def derive_async_database_url(self) -> "Settings":
        """
        Auto-derive ASYNC_DATABASE_URL from DATABASE_URL if not explicitly set.
        Railway injects DATABASE_URL as postgresql://... so we swap the scheme
        to postgresql+asyncpg:// for SQLAlchemy's async engine.
        """
        if not self.ASYNC_DATABASE_URL:
            url = self.DATABASE_URL
            # Replace any postgresql:// or postgres:// with postgresql+asyncpg://
            self.ASYNC_DATABASE_URL = (
                url
                .replace("postgresql://", "postgresql+asyncpg://", 1)
                .replace("postgres://", "postgresql+asyncpg://", 1)
            )
        return self

    class Config:
        # Tell pydantic-settings to read from the .env file
        env_file = ".env"


# Single shared instance — import this everywhere
settings = Settings()
