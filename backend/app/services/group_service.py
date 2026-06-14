# app/services/group_service.py
#
# Business logic for groups and membership.
# All rules about who can do what live here.

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group, GroupStatus
from app.models.group_member import MemberRole
from app.models.user import User
from app.repositories.group_repo import (
    close_group,
    create_group,
    get_group_by_id,
    update_group,
)
from app.repositories.member_repo import (
    add_member,
    get_active_members,
    get_active_members_with_users,
    get_membership,
    get_user_groups_with_membership,
    promote_to_admin,
    set_member_left,
)
from app.schemas.group import GroupListItem, GroupOut
from app.schemas.member import MemberOut


# ── HELPERS ──────────────────────────────────────────────────────

async def get_group_or_404(db: AsyncSession, group_id: UUID) -> Group:
    """Fetches a group by ID, raises 404 if it doesn't exist."""
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


async def require_active_group(group: Group) -> None:
    """Raises 403 if the group is CLOSED (no changes allowed on closed groups)."""
    if group.status == GroupStatus.CLOSED:
        raise HTTPException(status_code=403, detail="This group is closed and cannot be modified")


async def require_admin(db: AsyncSession, group_id: UUID, user_id: UUID) -> None:
    """Raises 403 if the user is not an admin of the group."""
    membership = await get_membership(db, group_id, user_id)
    if not membership or membership.left_at is not None:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    if membership.role != MemberRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only group admins can perform this action")


async def require_active_member(db: AsyncSession, group_id: UUID, user_id: UUID):
    """Returns the membership if user is an active member, else raises 403."""
    membership = await get_membership(db, group_id, user_id)
    if not membership or membership.left_at is not None:
        raise HTTPException(status_code=403, detail="You are not an active member of this group")
    return membership


# ── SERVICES ─────────────────────────────────────────────────────

async def create_new_group(
    db: AsyncSession,
    name: str,
    description: str | None,
    base_currency: str,
    current_user: User,
) -> GroupOut:
    """
    Creates a new group and automatically adds the creator as the ADMIN.
    """
    group = await create_group(
        db,
        name=name,
        description=description,
        base_currency=base_currency,
        created_by_user_id=current_user.id,
    )

    # Add creator as admin immediately
    now = datetime.now(timezone.utc)
    await add_member(db, group_id=group.id, user_id=current_user.id, role=MemberRole.ADMIN, joined_at=now)

    return await get_group_detail(db, group.id, current_user.id)


async def get_user_group_list(db: AsyncSession, user_id: UUID) -> list[GroupListItem]:
    """
    Returns a summary list of all groups the user is currently active in.
    Used on the dashboard.
    """
    rows = await get_user_groups_with_membership(db, user_id)

    result = []
    for membership, group in rows:
        # Count active members for each group (separate query per group — acceptable at this scale)
        active_members = await get_active_members(db, group.id)
        result.append(GroupListItem(
            id=group.id,
            name=group.name,
            base_currency=group.base_currency,
            status=group.status.value,
            my_role=membership.role.value,
            member_count=len(active_members),
        ))

    return result


async def get_group_detail(db: AsyncSession, group_id: UUID, current_user_id: UUID) -> GroupOut:
    """
    Returns full group details including all active members.
    Used on the group page.
    """
    group = await get_group_or_404(db, group_id)

    # Get the current user's membership to find their role
    my_membership = await get_membership(db, group_id, current_user_id)
    if not my_membership or my_membership.left_at is not None:
        raise HTTPException(status_code=403, detail="You are not an active member of this group")

    # Get all active members with their user info (name, email)
    member_rows = await get_active_members_with_users(db, group_id)

    members = [
        MemberOut(
            user_id=member.user_id,
            display_name=user.display_name,
            email=user.email,
            role=member.role.value,
            joined_at=member.joined_at,
            left_at=member.left_at,
        )
        for member, user in member_rows
    ]

    return GroupOut(
        id=group.id,
        name=group.name,
        description=group.description,
        base_currency=group.base_currency,
        currency_locked=group.currency_locked,
        status=group.status.value,
        my_role=my_membership.role.value,
        members=members,
        created_at=group.created_at,
    )


async def update_group_info(
    db: AsyncSession,
    group_id: UUID,
    current_user: User,
    name: str | None,
    description: str | None,
) -> GroupOut:
    """Updates the group's name and/or description. Admin only."""
    group = await get_group_or_404(db, group_id)
    await require_active_group(group)
    await require_admin(db, group_id, current_user.id)

    await update_group(db, group, name=name, description=description)
    return await get_group_detail(db, group_id, current_user.id)


async def leave_group(db: AsyncSession, group_id: UUID, current_user: User) -> dict:
    """
    Removes the current user from the group.

    Admin transfer rule:
      If the leaving user is the ADMIN, the next oldest active member
      is automatically promoted to ADMIN.

    If the leaving user is the LAST member, the group is CLOSED.
    """
    group = await get_group_or_404(db, group_id)
    await require_active_group(group)
    my_membership = await require_active_member(db, group_id, current_user.id)

    # Get all active members BEFORE marking this user as left
    active_members = await get_active_members(db, group_id)

    # Mark the user as left
    await set_member_left(db, my_membership)

    # Remaining active members (exclude the one who just left)
    remaining = [m for m in active_members if m.user_id != current_user.id]

    if not remaining:
        # No one left — close the group
        await close_group(db, group)
        return {"message": "You have left the group. The group has been closed as there are no remaining members."}

    if my_membership.role == MemberRole.ADMIN:
        # Transfer admin to the member who joined earliest
        # (already sorted by joined_at in get_active_members)
        next_admin = remaining[0]
        await promote_to_admin(db, next_admin)
        return {"message": "You have left the group. Admin role has been transferred to the next member."}

    return {"message": "You have left the group."}


async def remove_member(
    db: AsyncSession,
    group_id: UUID,
    target_user_id: UUID,
    current_user: User,
) -> dict:
    """
    Admin removes another member from the group.
    An admin cannot remove themselves — they must use leave_group instead.
    """
    group = await get_group_or_404(db, group_id)
    await require_active_group(group)
    await require_admin(db, group_id, current_user.id)

    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Use the leave endpoint to remove yourself from the group")

    target_membership = await get_membership(db, group_id, target_user_id)
    if not target_membership or target_membership.left_at is not None:
        raise HTTPException(status_code=404, detail="This user is not an active member of the group")

    await set_member_left(db, target_membership)
    return {"message": "Member removed from the group."}


async def delete_group(db: AsyncSession, group_id: UUID, current_user: User) -> dict:
    """
    Closes the group permanently. Admin only.
    All data (expenses, settlements) is preserved — the group just becomes read-only.
    """
    group = await get_group_or_404(db, group_id)
    await require_active_group(group)
    await require_admin(db, group_id, current_user.id)

    await close_group(db, group)
    return {"message": "Group has been closed. All history is preserved."}
