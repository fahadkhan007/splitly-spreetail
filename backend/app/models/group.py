# app/models/group.py
#
# A Group is the main container for shared expenses.
# Examples: "Flat 4B", "Goa Trip 2026", "Office Lunch Group"
#
# Key rules:
#   - base_currency is set when the group is created and cannot be changed
#     once the first expense is added (currency_locked = True)
#   - A CLOSED group keeps all its data but accepts no new expenses/settlements

import enum
import uuid

from sqlalchemy import Column, String, Boolean, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class GroupStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"   # Group is active, members can add expenses
    CLOSED = "CLOSED"   # Group is closed, all data preserved but read-only


class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(100), nullable=False)

    # Optional description shown on the group page
    description = Column(Text, nullable=True)

    # ISO 4217 currency code e.g. 'INR', 'USD', 'EUR'
    # All expense amounts are converted to this currency for balance calculations
    base_currency = Column(String(3), nullable=False)

    # Becomes True when the first expense is added.
    # After that, the base_currency cannot be changed.
    currency_locked = Column(Boolean, nullable=False, default=False)

    status = Column(Enum(GroupStatus), nullable=False, default=GroupStatus.ACTIVE)

    # Who originally created the group (may change when admin leaves)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
