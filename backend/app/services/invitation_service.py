# app/services/invitation_service.py
#
# Business logic for sending and accepting group invitations.
#
# Two invitation flows:
#
# Flow A — Existing user receives invite:
#   Admin sends invite → user gets email → clicks "Accept" link →
#   frontend calls POST /invitations/accept?token=... (while logged in) →
#   user is added to the group
#
# Flow B — New user receives invite:
#   Admin sends invite → unregistered email gets email → clicks "Register" link →
#   frontend shows register page WITH the invite_token pre-filled →
#   user registers → registration code detects invite_token → user added to group

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.email import send_group_invitation_email
from app.core.security import create_invite_token, decode_token
from app.models.group_member import MemberRole
from app.models.invitation import InvitationStatus
from app.models.user import User
from app.repositories.group_repo import get_group_by_id
from app.repositories.invitation_repo import (
    cancel_invitation,
    create_invitation,
    get_group_invitations,
    get_invitation_by_token,
    get_pending_invitation,
    mark_invitation_accepted,
)
from app.repositories.member_repo import (
    add_member,
    get_active_members,
    get_membership,
)
from app.repositories.user_repo import get_user_by_email
from app.schemas.invitation import InvitationOut
from app.services.group_service import require_admin, require_active_group


async def send_invite(
    db: AsyncSession,
    group_id: UUID,
    invited_email: str,
    current_user: User,
) -> InvitationOut:
    """
    Sends a group invitation email to the given address.

    Rules:
    - Only group admins can invite
    - Cannot invite someone who is already an active member
    - If a PENDING invite already exists for this email, it is cancelled
      and a new one is created (resend behavior)
    - The email link differs based on whether the invited email has an account:
        Has account  → link goes to /join?token=...  (they accept while logged in)
        No account   → link goes to /register?invite_token=...  (they register first)
    """
    # Validate group exists and is active
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await require_active_group(group)

    # Only admins can invite
    await require_admin(db, group_id, current_user.id)

    # Check if the invited email already belongs to an active group member
    invited_user = await get_user_by_email(db, invited_email)
    if invited_user:
        existing_membership = await get_membership(db, group_id, invited_user.id)
        if existing_membership and existing_membership.left_at is None:
            raise HTTPException(
                status_code=400,
                detail="This person is already an active member of the group"
            )

    # Cancel any existing PENDING invite for this email in this group
    existing_invite = await get_pending_invitation(db, group_id, invited_email)
    if existing_invite:
        await cancel_invitation(db, existing_invite)

    # Create a new JWT invite token (7 days expiry)
    token_str = create_invite_token(str(group_id), invited_email)

    # expires_at for the DB record (must match the JWT expiry)
    from datetime import timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Save the invitation to the database
    invitation = await create_invitation(
        db,
        group_id=group_id,
        invited_by_user_id=current_user.id,
        invited_email=invited_email,
        token=token_str,
        expires_at=expires_at,
    )

    # Build the invite link based on whether the person has an account
    if invited_user:
        # Existing user — send them to the join page (they'll be logged in)
        invite_link = f"{settings.FRONTEND_URL}/invitations/accept?token={token_str}"
    else:
        # New user — send them to register, with the invite token included
        invite_link = f"{settings.FRONTEND_URL}/register?invite_token={token_str}"

    # Send the email
    send_group_invitation_email(
        to_email=invited_email,
        group_name=group.name,
        invited_by=current_user.display_name,
        invite_link=invite_link,
    )

    return InvitationOut.model_validate(invitation)


async def accept_invite(
    db: AsyncSession,
    token: str,
    current_user: User,
) -> dict:
    """
    Called when an existing logged-in user clicks the invitation link.

    Steps:
    1. Decode and validate the JWT token
    2. Find the invitation record in the DB
    3. Check the token is PENDING (not expired, accepted, or cancelled)
    4. Check the current user's email matches the invited email
    5. Add the user to the group
    6. Mark the invitation as ACCEPTED
    """
    # Step 1: Decode the JWT
    payload = decode_token(token)
    if not payload or payload.get("type") != "group_invite":
        raise HTTPException(status_code=400, detail="Invalid or expired invitation link")

    invited_email = payload.get("invited_email")
    group_id = UUID(payload.get("group_id"))

    # Step 2: Find the DB record
    invitation = await get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # Step 3: Check invitation is still PENDING
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"This invitation has already been {invitation.status.value.lower()}"
        )

    # Step 4: The logged-in user's email must match the invitation's email
    if current_user.email.lower() != invited_email.lower():
        raise HTTPException(
            status_code=403,
            detail="This invitation was sent to a different email address"
        )

    # Check group is still active
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await require_active_group(group)

    # Check user isn't already a member
    existing = await get_membership(db, group_id, current_user.id)
    if existing and existing.left_at is None:
        raise HTTPException(status_code=400, detail="You are already a member of this group")

    # Step 5: Add user to the group
    now = datetime.now(timezone.utc)
    await add_member(db, group_id=group_id, user_id=current_user.id, role=MemberRole.MEMBER, joined_at=now)

    # Step 6: Mark invitation as accepted
    await mark_invitation_accepted(db, invitation, current_user.id)

    return {"message": f"You have joined the group '{group.name}' successfully!"}


async def accept_invite_on_registration(
    db: AsyncSession,
    token: str,
    new_user: User,
) -> None:
    """
    Called automatically at the end of registration when the user signed up
    via an invitation link. Adds the new user to the group.

    We don't raise errors here — if the invite is invalid we just skip it
    silently (the user is already registered, don't block their account).
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "group_invite":
        return  # Invalid token — just skip, user is registered anyway

    invited_email = payload.get("invited_email", "")
    group_id_str = payload.get("group_id")

    # Email in invite must match the registering user's email
    if new_user.email.lower() != invited_email.lower():
        return

    try:
        group_id = UUID(group_id_str)
        invitation = await get_invitation_by_token(db, token)

        if not invitation or invitation.status != InvitationStatus.PENDING:
            return

        group = await get_group_by_id(db, group_id)
        if not group:
            return

        now = datetime.now(timezone.utc)
        await add_member(db, group_id=group_id, user_id=new_user.id, role=MemberRole.MEMBER, joined_at=now)
        await mark_invitation_accepted(db, invitation, new_user.id)

    except Exception:
        # Never block registration due to an invite processing error
        return


async def list_group_invitations(
    db: AsyncSession,
    group_id: UUID,
    current_user: User,
) -> list[InvitationOut]:
    """Returns all pending invitations for a group. Admin only."""
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await require_admin(db, group_id, current_user.id)

    invitations = await get_group_invitations(db, group_id)
    return [InvitationOut.model_validate(inv) for inv in invitations]
