# app/schemas/expense.py

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class SplitInput(BaseModel):
    """
    One entry in the splits list when creating an expense.
    The meaning of 'value' depends on split_type:
      EQUAL      — value is ignored (everyone gets equal share)
      UNEQUAL    — value is the exact amount this person owes (in base currency)
      PERCENTAGE — value is the percentage this person owes (e.g. 33.33)
      SHARE      — value is the number of shares this person has (e.g. 2)
    """
    user_id: UUID
    value: float = 0.0


class ExpenseCreate(BaseModel):
    description: str
    notes: str | None = None
    amount: float                  # original amount as entered
    currency: str                  # 3-letter ISO code (e.g. 'INR', 'USD')
    split_type: str                # EQUAL | UNEQUAL | PERCENTAGE | SHARE
    expense_date: date
    paid_by_user_id: UUID
    splits: list[SplitInput] = []  # empty = EQUAL split among all active members

    @field_validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("currency")
    def currency_must_be_3_letters(cls, v):
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code like INR or USD")
        return v.upper()

    @field_validator("split_type")
    def valid_split_type(cls, v):
        allowed = ["EQUAL", "UNEQUAL", "PERCENTAGE", "SHARE"]
        if v.upper() not in allowed:
            raise ValueError(f"split_type must be one of: {', '.join(allowed)}")
        return v.upper()


class ExpenseUpdate(BaseModel):
    """All fields optional — only provided fields will be updated."""
    description: str | None = None
    notes: str | None = None
    expense_date: date | None = None


class ExpenseSplitOut(BaseModel):
    user_id: UUID
    display_name: str
    amount_owed_base: float


class ExpenseOut(BaseModel):
    id: UUID
    group_id: UUID
    description: str
    notes: str | None
    paid_by_user_id: UUID
    paid_by_name: str
    amount_original: float
    currency_original: str
    amount_base: float
    fx_rate_used: float | None
    split_type: str
    expense_date: date
    splits: list[ExpenseSplitOut]
    created_at: datetime


class ExpenseListItem(BaseModel):
    id: UUID
    description: str
    paid_by_user_id: UUID
    paid_by_name: str
    amount_original: float
    currency_original: str
    amount_base: float
    split_type: str
    expense_date: date
    created_at: datetime
