# app/schemas/report.py

from datetime import date
from uuid import UUID

from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    category: str
    expense_count: int
    total_amount: float   # in base currency


class MemberSummary(BaseModel):
    user_id: UUID
    display_name: str
    total_paid: float     # total amount this member paid across all expenses
    total_owed: float     # total amount this member owes across all splits
    net_balance: float    # total_paid - total_owed


class GroupSummaryReport(BaseModel):
    """Overall group statistics."""
    group_id: UUID
    base_currency: str
    total_expenses: int
    total_amount: float
    total_settlements: int
    total_settled_amount: float
    by_category: list[CategoryBreakdown]
    by_member: list[MemberSummary]


class MonthlyEntry(BaseModel):
    year: int
    month: int
    month_label: str      # e.g. "June 2024"
    expense_count: int
    total_amount: float   # in base currency


class MonthlyReport(BaseModel):
    group_id: UUID
    base_currency: str
    monthly_data: list[MonthlyEntry]  # sorted newest first
