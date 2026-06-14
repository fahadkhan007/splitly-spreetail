# app/schemas/balance.py

from uuid import UUID
from pydantic import BaseModel


class UserBalance(BaseModel):
    user_id: UUID
    display_name: str
    net_balance: float
    # Positive = this person is owed money by others
    # Negative = this person owes money to others


class DebtItem(BaseModel):
    """One simplified payment: 'from_name owes to_name this amount'"""
    from_user_id: UUID
    from_name: str
    to_user_id: UUID
    to_name: str
    amount: float  # always positive, in base currency


class GroupBalances(BaseModel):
    group_id: UUID
    base_currency: str
    balances: list[UserBalance]
    simplified_debts: list[DebtItem]  # greedy-simplified list of who pays whom
