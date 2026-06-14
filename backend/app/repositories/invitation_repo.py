# app/repositories/invitation_repo.py
#
# All database queries related to invitations.

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invitation import Invitation, InvitationStatus


async def create_invitation(
    db: AsyncSession,
    group_id: UUID,
    invited_by_user_id: UUID,
    invited_email: str,
    token: str,
    expires_at: datetime,
) -> Invitation:
    """Creates a new invitation record in the database."""
    invitation = Invitation(
        group_id=group_id,
        invited_by_user_id=invited_by_user_id,
        invited_email=invited_email,
        token=token,
        expires_at=expires_at,
        status=InvitationStatus.PENDING,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    return invitation


async def get_invitation_by_token(db: AsyncSession, token: str) -> Invitation | None:
    """Finds an invitation by its unique token string."""
    result = await db.execute(
        select(Invitation).where(Invitation.token == token)
    )
    return result.scalar_one_or_none()


async def get_pending_invitation(
    db: AsyncSession,
    group_id: UUID,
    email: str,
) -> Invitation | None:
    """
    Checks if there is already a PENDING invitation for this email in this group.
    Used to avoid duplicate invites and to cancel old ones on resend.
    """
    result = await db.execute(
        select(Invitation).where(
            Invitation.group_id == group_id,
            Invitation.invited_email == email,
            Invitation.status == InvitationStatus.PENDING,
        )
    )
    return result.scalar_one_or_none()


async def get_group_invitations(db: AsyncSession, group_id: UUID) -> list[Invitation]:
    """Returns all PENDING invitations for a group (shown in the admin panel)."""
    result = await db.execute(
        select(Invitation).where(
            Invitation.group_id == group_id,
            Invitation.status == InvitationStatus.PENDING,
        ).order_by(Invitation.created_at.desc())
    )
    return list(result.scalars().all())


async def cancel_invitation(db: AsyncSession, invitation: Invitation) -> Invitation:
    """Marks an invitation as CANCELLED (used when admin resends an invite)."""
    invitation.status = InvitationStatus.CANCELLED
    await db.commit()
    await db.refresh(invitation)
    return invitation


async def mark_invitation_accepted(
    db: AsyncSession,
    invitation: Invitation,
    accepted_by_user_id: UUID,
) -> Invitation:
    """Marks an invitation as ACCEPTED after a user joins the group."""
    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_by_user_id = accepted_by_user_id
    await db.commit()
    await db.refresh(invitation)
    return invitation
