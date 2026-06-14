# app/routers/groups.py
#
# HTTP routes for groups and membership management.
#
# Routes:
#   POST   /groups                              — create a new group
#   GET    /groups                              — list my groups
#   GET    /groups/{group_id}                   — get group details
#   PATCH  /groups/{group_id}                   — update group info (admin only)
#   DELETE /groups/{group_id}                   — close the group (admin only)
#   POST   /groups/{group_id}/leave             — leave a group
#   DELETE /groups/{group_id}/members/{user_id} — remove a member (admin only)

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_verified_email
from app.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.group import GroupCreate, GroupListItem, GroupOut, GroupUpdate
from app.services.group_service import (
    create_new_group,
    delete_group,
    get_group_detail,
    get_user_group_list,
    leave_group,
    remove_member,
    update_group_info,
)

router = APIRouter()


@router.post("", response_model=GroupOut, status_code=201)
async def create_group(
    body: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_verified_email),  # email must be verified
):
    """Creates a new group. The creator automatically becomes the admin."""
    return await create_new_group(
        db,
        name=body.name,
        description=body.description,
        base_currency=body.base_currency,
        current_user=current_user,
    )


@router.get("", response_model=list[GroupListItem])
async def list_my_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all groups the current user is an active member of."""
    return await get_user_group_list(db, current_user.id)


@router.get("/{group_id}", response_model=GroupOut)
async def get_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns full details for a group including all active members."""
    return await get_group_detail(db, group_id, current_user.id)


@router.patch("/{group_id}", response_model=GroupOut)
async def update_group(
    group_id: UUID,
    body: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates the group name and/or description. Admin only."""
    return await update_group_info(
        db,
        group_id=group_id,
        current_user=current_user,
        name=body.name,
        description=body.description,
    )


@router.post("/{group_id}/leave", response_model=MessageResponse)
async def leave(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Removes the current user from the group.
    If the user is the admin, the next oldest member becomes admin automatically.
    If the user is the last member, the group is closed.
    """
    return await leave_group(db, group_id, current_user)


@router.delete("/{group_id}/members/{user_id}", response_model=MessageResponse)
async def kick_member(
    group_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Removes another member from the group. Admin only."""
    return await remove_member(db, group_id, user_id, current_user)


@router.delete("/{group_id}", response_model=MessageResponse)
async def close_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Closes the group. All data is preserved but no new expenses can be added. Admin only."""
    return await delete_group(db, group_id, current_user)
