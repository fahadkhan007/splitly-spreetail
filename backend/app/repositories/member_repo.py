# app/repositories/member_repo.py
#
# All database queries related to group membership.

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_member import GroupMember, MemberRole
from app.models.user import User


async def add_member(
    db: AsyncSession,
    group_id: UUID,
    user_id: UUID,
    role: MemberRole,
    joined_at: datetime,
) -> GroupMember:
    """Adds a user to a group. Used when a group is created or an invite is accepted."""
    member = GroupMember(
        group_id=group_id,
        user_id=user_id,
        role=role,
        joined_at=joined_at,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def get_membership(
    db: AsyncSession,
    group_id: UUID,
    user_id: UUID,
) -> GroupMember | None:
    """
    Returns the membership record for a user in a group.
    Returns None if the user is not in the group (or never was).
    """
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_active_members(db: AsyncSession, group_id: UUID) -> list[GroupMember]:
    """Returns all members who are currently active (have not left the group)."""
    result = await db.execute(
        select(GroupMember)
        .where(
            GroupMember.group_id == group_id,
            GroupMember.left_at == None,  # noqa: E711 — SQLAlchemy requires ==, not `is`
        )
        .order_by(GroupMember.joined_at)  # oldest member first
    )
    return list(result.scalars().all())


async def get_active_members_with_users(
    db: AsyncSession,
    group_id: UUID,
) -> list[tuple[GroupMember, User]]:
    """
    Returns active members joined with their user info (name, email).
    Used to build the MemberOut list in group responses.
    """
    result = await db.execute(
        select(GroupMember, User)
        .join(User, GroupMember.user_id == User.id)
        .where(
            GroupMember.group_id == group_id,
            GroupMember.left_at == None,  # noqa: E711
        )
        .order_by(GroupMember.joined_at)
    )
    return list(result.all())


async def get_all_members_with_users(
    db: AsyncSession,
    group_id: UUID,
) -> list[tuple[GroupMember, User]]:
    """
    Returns ALL members (active + who have left) with their user info.
    Used during CSV import to detect ghost members and fuzzy-match historical names.
    """
    result = await db.execute(
        select(GroupMember, User)
        .join(User, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.joined_at)
    )
    return list(result.all())



async def get_user_groups_with_membership(
    db: AsyncSession,
    user_id: UUID,
) -> list[tuple[GroupMember, "Group"]]:
    """
    Returns all active group memberships for a user,
    joined with the group details.
    Used to build the group list on the dashboard.
    """
    from app.models.group import Group  # local import avoids circular dependency

    result = await db.execute(
        select(GroupMember, Group)
        .join(Group, GroupMember.group_id == Group.id)
        .where(
            GroupMember.user_id == user_id,
            GroupMember.left_at == None,  # noqa: E711
        )
        .order_by(Group.name)
    )
    return list(result.all())


async def set_member_left(db: AsyncSession, membership: GroupMember) -> GroupMember:
    """Marks a member as having left the group by setting left_at to now."""
    membership.left_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(membership)
    return membership


async def promote_to_admin(db: AsyncSession, membership: GroupMember) -> GroupMember:
    """Promotes a member to admin. Used when the current admin leaves."""
    membership.role = MemberRole.ADMIN
    await db.commit()
    await db.refresh(membership)
    return membership
