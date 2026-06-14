# app/repositories/group_repo.py
#
# All database queries related to groups.
# No business logic here — only reads and writes.

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group, GroupStatus


async def create_group(
    db: AsyncSession,
    name: str,
    description: str | None,
    base_currency: str,
    created_by_user_id: UUID,
) -> Group:
    """Creates a new group and saves it to the database."""
    group = Group(
        name=name,
        description=description,
        base_currency=base_currency,
        created_by_user_id=created_by_user_id,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def get_group_by_id(db: AsyncSession, group_id: UUID) -> Group | None:
    """Finds a group by its UUID. Returns None if not found."""
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    return result.scalar_one_or_none()


async def update_group(
    db: AsyncSession,
    group: Group,
    name: str | None,
    description: str | None,
) -> Group:
    """Updates the group's name and/or description."""
    if name is not None:
        group.name = name
    if description is not None:
        group.description = description
    await db.commit()
    await db.refresh(group)
    return group


async def close_group(db: AsyncSession, group: Group) -> Group:
    """Sets the group status to CLOSED. All data is preserved."""
    group.status = GroupStatus.CLOSED
    await db.commit()
    await db.refresh(group)
    return group


async def lock_group_currency(db: AsyncSession, group: Group) -> Group:
    """
    Locks the group's base currency.
    Called automatically when the first expense is added to the group.
    After this, base_currency cannot be changed.
    """
    group.currency_locked = True
    await db.commit()
    await db.refresh(group)
    return group
