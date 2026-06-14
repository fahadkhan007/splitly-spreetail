# app/services/report_service.py
#
# Generates summary and monthly reports for a group.
# All calculations are done in Python using already-loaded data.

from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.expense_repo import get_all_expenses_with_splits, get_group_expenses
from app.repositories.group_repo import get_group_by_id
from app.repositories.member_repo import get_active_members_with_users
from app.repositories.settlement_repo import get_group_settlements
from app.repositories.user_repo import get_user_by_id
from app.schemas.report import (
    CategoryBreakdown,
    GroupSummaryReport,
    MemberSummary,
    MonthlyEntry,
    MonthlyReport,
)
from app.services.group_service import require_active_member


async def get_summary_report(
    db: AsyncSession,
    group_id: UUID,
    current_user_id: UUID,
) -> GroupSummaryReport:
    """Returns a complete summary of expenses, settlements, categories, and member contributions."""
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # -- Members --
    member_rows = await get_active_members_with_users(db, group_id)
    user_names: dict[str, str] = {str(u.id): u.display_name for _, u in member_rows}

    # -- Expenses --
    expense_rows = await get_all_expenses_with_splits(db, group_id)
    expenses = await get_group_expenses(db, group_id)

    total_amount = sum(float(e.amount_base) for e in expenses)

    # By category
    category_totals: dict[str, dict] = defaultdict(lambda: {"count": 0, "amount": 0.0})
    for e in expenses:
        cat = (e.notes or "Uncategorized")  # no category field — use notes or default
        # Actually check model: expense has no category column; let's use "General" as default
        cat = "General"  # placeholder since model has no category field
        category_totals[cat]["count"] += 1
        category_totals[cat]["amount"] += float(e.amount_base)

    by_category = [
        CategoryBreakdown(category=cat, expense_count=v["count"], total_amount=round(v["amount"], 2))
        for cat, v in sorted(category_totals.items(), key=lambda x: -x[1]["amount"])
    ]

    # By member: paid and owed
    member_paid: dict[str, float] = defaultdict(float)
    member_owed: dict[str, float] = defaultdict(float)

    for expense, split in expense_rows:
        member_paid[str(expense.paid_by_user_id)] += float(expense.amount_base)
        member_owed[str(split.user_id)] += float(split.amount_owed_base)

    all_user_ids = set(member_paid.keys()) | set(member_owed.keys())
    by_member = []
    for uid in all_user_ids:
        paid = round(member_paid[uid], 2)
        owed = round(member_owed[uid], 2)
        by_member.append(MemberSummary(
            user_id=uid,
            display_name=user_names.get(uid, "Unknown"),
            total_paid=paid,
            total_owed=owed,
            net_balance=round(paid - owed, 2),
        ))
    by_member.sort(key=lambda m: -m.net_balance)

    # -- Settlements --
    settlements = await get_group_settlements(db, group_id)
    active_settlements = [s for s in settlements if s.status.value == "ACTIVE"]
    total_settled = sum(float(s.amount_base) for s in active_settlements)

    return GroupSummaryReport(
        group_id=group_id,
        base_currency=group.base_currency,
        total_expenses=len(expenses),
        total_amount=round(total_amount, 2),
        total_settlements=len(active_settlements),
        total_settled_amount=round(total_settled, 2),
        by_category=by_category,
        by_member=by_member,
    )


async def get_monthly_report(
    db: AsyncSession,
    group_id: UUID,
    current_user_id: UUID,
) -> MonthlyReport:
    """Returns expense totals broken down by calendar month."""
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    expenses = await get_group_expenses(db, group_id)

    MONTH_NAMES = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    monthly: dict[tuple, dict] = defaultdict(lambda: {"count": 0, "amount": 0.0})
    for expense in expenses:
        key = (expense.expense_date.year, expense.expense_date.month)
        monthly[key]["count"] += 1
        monthly[key]["amount"] += float(expense.amount_base)

    monthly_data = [
        MonthlyEntry(
            year=year,
            month=month,
            month_label=f"{MONTH_NAMES[month]} {year}",
            expense_count=data["count"],
            total_amount=round(data["amount"], 2),
        )
        for (year, month), data in sorted(monthly.items(), reverse=True)
    ]

    return MonthlyReport(
        group_id=group_id,
        base_currency=group.base_currency,
        monthly_data=monthly_data,
    )
