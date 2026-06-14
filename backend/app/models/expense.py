# app/models/expense.py
#
# Expense stores every shared expense added to a group.
#
# Currency handling:
#   - amount_original: the number the user typed (in whatever currency they chose)
#   - currency_original: the currency they chose (e.g. 'USD')
#   - amount_base: converted to the group's base currency (e.g. 'INR')
#   - fx_rate_used: the exchange rate used for conversion (stored for audit)
#
# If the expense is in the group's base currency, amount_base = amount_original
# and fx_rate_used = 1.0

import enum
import uuid

from sqlalchemy import Boolean, Column, String, Text, Date, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class SplitType(str, enum.Enum):
    EQUAL = "EQUAL"           # Split evenly among all participants
    UNEQUAL = "UNEQUAL"       # Each person's amount is specified manually
    PERCENTAGE = "PERCENTAGE" # Each person owes a % of the total (must sum to 100)
    SHARE = "SHARE"           # Each person gets a ratio (e.g. 2:1:1)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which group this expense belongs to
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False, index=True)

    # Who actually paid the bill
    paid_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    description = Column(String(500), nullable=False)

    # The original amount and currency as the user entered them
    amount_original = Column(Numeric(12, 2), nullable=False)
    currency_original = Column(String(3), nullable=False)

    # The amount converted to the group's base currency.
    # This is the value used for ALL balance calculations.
    amount_base = Column(Numeric(12, 2), nullable=False)

    # The exchange rate used. NULL if amount_original currency == group base currency.
    fx_rate_used = Column(Numeric(18, 6), nullable=True)

    # The date the expense occurred (not when it was entered into the app)
    expense_date = Column(Date, nullable=False)

    split_type = Column(Enum(SplitType), nullable=False)

    # Optional notes (e.g. "Aisha was not present", "birthday dinner")
    notes = Column(Text, nullable=True)

    # If this expense was created via CSV import, link it to the import report
    import_id = Column(UUID(as_uuid=True), ForeignKey("import_reports.id"), nullable=True)

    # Who entered this expense into the app (may differ from paid_by_user_id)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Soft delete — we never hard-delete expenses; this flag hides them from all views
    is_deleted = Column(Boolean, default=False, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
