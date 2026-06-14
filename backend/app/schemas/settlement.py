# app/schemas/settlement.py

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class SettlementCreate(BaseModel):
    payer_user_id: UUID     # who sent the money
    payee_user_id: UUID     # who received the money
    amount: float
    currency: str
    notes: str | None = None
    settlement_date: date   # when the payment actually happened

    @field_validator("amount")
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("currency")
    def currency_3_letters(cls, v):
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


class SettlementOut(BaseModel):
    id: UUID
    group_id: UUID
    payer_user_id: UUID
    payer_name: str
    payee_user_id: UUID
    payee_name: str
    amount_original: float
    currency_original: str
    amount_base: float
    fx_rate_used: float | None
    settlement_date: date
    status: str
    notes: str | None
    created_at: datetime
