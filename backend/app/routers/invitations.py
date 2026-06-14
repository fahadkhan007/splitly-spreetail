# app/routers/invitations.py
#
# HTTP routes for group invitations.
#
# Routes:
#   POST /groups/{group_id}/invitations         — send an invite (admin only)
#   GET  /groups/{group_id}/invitations         — list pending invites (admin only)
#   POST /invitations/accept?token=...          — accept an invite (logged-in user)

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_verified_email
from app.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.invitation import InvitationOut, InviteRequest
from app.services.invitation_service import (
    accept_invite,
    list_group_invitations,
    send_invite,
)

router = APIRouter()


@router.post("/groups/{group_id}/invitations", response_model=InvitationOut, status_code=201)
async def send_group_invite(
    group_id: UUID,
    body: InviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_verified_email),  # must have verified email to invite
):
    """
    Sends a group invitation email to the specified address.
    If a pending invite already exists for this email, it is cancelled and a new one is sent.
    Admin only.
    """
    return await send_invite(db, group_id=group_id, invited_email=body.email, current_user=current_user)


@router.get("/groups/{group_id}/invitations", response_model=list[InvitationOut])
async def get_group_invitations(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all pending invitations for a group. Admin only."""
    return await list_group_invitations(db, group_id=group_id, current_user=current_user)


@router.post("/invitations/accept", response_model=MessageResponse)
async def accept_invitation(
    token: str = Query(..., description="The invite token from the email link"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts a group invitation. The user must be logged in.
    The token comes from the invite link: /invitations/accept?token=...

    For new users who registered via the invite link, acceptance happens
    automatically during registration — they don't need to call this endpoint.
    """
    return await accept_invite(db, token=token, current_user=current_user)
