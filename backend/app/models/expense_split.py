# app/models/expense_split.py
#
# ExpenseSplit stores each person's share of a single expense.
# One Expense has many ExpenseSplits (one per participant).
#
# How amount_owed_base is calculated per split type:
#   EQUAL:      total / number_of_participants
#   UNEQUAL:    the specific amount entered for this person
#   PERCENTAGE: total * (percentage / 100)    [share_value = the percentage]
#   SHARE:      total * (ratio / sum_of_all_ratios)  [share_value = the ratio]
#
# Validation rule: SUM of all amount_owed_base for one expense must equal
# the expense's amount_base (within ±0.01 rounding tolerance)

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # The expense this split belongs to
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id"), nullable=False, index=True)

    # The person who owes this share
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # How much this person owes, in the group's base currency.
    # This is used directly in balance calculations.
    amount_owed_base = Column(Numeric(12, 2), nullable=False)

    # The raw value as entered by the user:
    #   - For PERCENTAGE split: stores the percentage (e.g. 33.33)
    #   - For SHARE split:      stores the ratio value (e.g. 2)
    #   - For EQUAL split:      NULL (no raw value needed)
    #   - For UNEQUAL split:    NULL (amount_owed_base IS the raw value)
    share_value = Column(Numeric(10, 4), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
