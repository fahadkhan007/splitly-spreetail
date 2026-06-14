# app/database.py
#
# Sets up the database connection for the entire application.
#
# Three things this file provides:
#   1. engine       — the actual connection to PostgreSQL
#   2. Base         — parent class that all DB models inherit from
#   3. get_db()     — a FastAPI dependency that gives each request
#                     its own database session and closes it when done

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.config import settings


# ── 1. ENGINE ────────────────────────────────────────────────────
# The engine manages the pool of connections to PostgreSQL.
# echo=True prints every SQL query to the console (helpful while developing).
# Set echo=False in production.
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=True,
)


# ── 2. SESSION FACTORY ───────────────────────────────────────────
# AsyncSessionLocal is a factory that creates new database sessions.
# expire_on_commit=False means we can still read data from objects
# after we commit a transaction (safer default for FastAPI).
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# ── 3. BASE MODEL ────────────────────────────────────────────────
# All SQLAlchemy table classes will inherit from this Base.
# Example:
#   class User(Base):
#       __tablename__ = "users"
#       ...
Base = declarative_base()


# ── 4. DATABASE DEPENDENCY ───────────────────────────────────────
# FastAPI calls this function for every request that needs the DB.
# The `yield` makes it a context manager:
#   - Opens a session before the route runs
#   - Closes the session after the route finishes (even on errors)
#
# Usage in a router:
#   async def get_users(db: AsyncSession = Depends(get_db)):
#       ...
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
