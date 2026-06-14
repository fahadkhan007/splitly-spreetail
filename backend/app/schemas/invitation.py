# app/schemas/invitation.py
#
# Request and response shapes for group invitations.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class InviteRequest(BaseModel):
    """Body for POST /groups/{group_id}/invitations"""
    email: EmailStr


class InvitationOut(BaseModel):
    """Represents a single invitation record."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    invited_email: str
    status: str         # 'PENDING', 'ACCEPTED', 'EXPIRED', 'CANCELLED'
    expires_at: datetime
    created_at: datetime
