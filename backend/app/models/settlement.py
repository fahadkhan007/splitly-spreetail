# app/models/settlement.py
#
# Settlement records a payment made between two people to reduce a debt.
# Example: "Rohan pays Priya ₹500 to settle what he owes her"
#
# Key rules:
#   - Settlements can NEVER be permanently deleted
#   - A settlement can only be VOIDED (soft cancel) by the person who recorded it
#     or by a group admin
#   - VOIDED settlements are completely ignored in balance calculations
#   - The original record always stays in the database for audit purposes

import enum
import uuid

from sqlalchemy import Column, String, Text, Date, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class SettlementStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"   # This settlement counts toward balances
    VOIDED = "VOIDED"   # Cancelled — ignored in all calculations


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which group this settlement belongs to
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False, index=True)

    # The person who sent the money
    payer_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # The person who received the money
    payee_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Original amount and currency as entered
    amount_original = Column(Numeric(12, 2), nullable=False)
    currency_original = Column(String(3), nullable=False)

    # Converted to group base currency — used in balance calculations
    amount_base = Column(Numeric(12, 2), nullable=False)
    fx_rate_used = Column(Numeric(18, 6), nullable=True)

    # The date the money was actually transferred
    settlement_date = Column(Date, nullable=False)

    status = Column(Enum(SettlementStatus), nullable=False, default=SettlementStatus.ACTIVE)

    notes = Column(Text, nullable=True)

    # Who recorded this settlement in the app
    recorded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Filled in when someone voids this settlement
    voided_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)

    # If this settlement was created via CSV import
    import_id = Column(UUID(as_uuid=True), ForeignKey("import_reports.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
