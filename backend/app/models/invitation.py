# app/models/invitation.py
#
# Invitation tracks every email invite sent to join a group.
#
# Flow:
#   1. Admin sends invite → new Invitation row created with status=PENDING
#   2. User clicks the link in the email → token is validated
#   3. If token is valid and not expired → status becomes ACCEPTED
#   4. If admin resends → old PENDING invite becomes CANCELLED, new one created
#   5. If 7 days pass without acceptance → treat as EXPIRED (checked in code)

import enum
import uuid

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class InvitationStatus(str, enum.Enum):
    PENDING = "PENDING"       # Sent but not yet accepted
    ACCEPTED = "ACCEPTED"     # User clicked the link and joined
    EXPIRED = "EXPIRED"       # 7 days passed without acceptance
    CANCELLED = "CANCELLED"   # Admin resent the invite (old one cancelled)


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which group this invite is for
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False, index=True)

    # Which admin sent the invite
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # The email address the invite was sent to
    invited_email = Column(String(255), nullable=False)

    # A unique random token embedded in the invite link URL.
    # We validate this token when the user clicks the link.
    token = Column(String(512), nullable=False, unique=True, index=True)

    status = Column(Enum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING)

    # The invite link stops working after this datetime
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Set when the invite is accepted — links the invite to the user who accepted it
    accepted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
