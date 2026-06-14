# app/models/group_member.py
#
# GroupMember tracks who is (or was) in a group and when.
#
# This is the most important table for balance calculations.
# The joined_at and left_at timestamps let us enforce the rule:
# "only count expenses that happened during a member's active period."
#
# Active member:  left_at IS NULL
# Former member:  left_at is set to the datetime they left

import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class MemberRole(str, enum.Enum):
    ADMIN = "ADMIN"     # Can invite, remove members, delete group, import CSV
    MEMBER = "MEMBER"   # Can view, add expenses, record settlements


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    role = Column(Enum(MemberRole), nullable=False, default=MemberRole.MEMBER)

    # When this person joined the group (or was added via CSV import)
    joined_at = Column(DateTime(timezone=True), nullable=False)

    # When this person left the group. NULL means they are still active.
    # Only expenses between joined_at and left_at count toward their balance.
    left_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        # A user can only have ONE membership record per group
        UniqueConstraint("group_id", "user_id", name="uq_group_user_membership"),
    )
