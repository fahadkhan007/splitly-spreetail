# app/repositories/user_repo.py
#
# All database queries related to users live here.
# This layer does NO business logic — it just reads and writes to the DB.
# Business logic lives in services/auth_service.py.

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserStatus


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Find a user by their email address. Returns None if not found."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Find a user by their UUID. Returns None if not found."""
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    display_name: str,
    password_hash: str,
) -> User:
    """
    Creates a new ACTIVE user with is_verified=False.
    The user must verify their email before some features are available.
    """
    new_user = User(
        email=email,
        display_name=display_name,
        password_hash=password_hash,
        is_verified=False,
        status=UserStatus.ACTIVE,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def mark_user_verified(db: AsyncSession, user: User) -> User:
    """Sets is_verified=True for a user after they click the verification link."""
    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return user
