# app/services/expense_service.py
#
# Business logic for creating, editing, and deleting expenses.
# Handles all 4 split types and currency conversion.

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.fx import get_exchange_rate
from app.models.expense import SplitType
from app.models.group_member import MemberRole
from app.models.user import User
from app.repositories.expense_repo import (
    create_expense,
    create_splits,
    delete_splits_for_expense,
    get_expense_by_id,
    get_expense_splits,
    get_group_expenses,
    soft_delete_expense,
)
from app.repositories.group_repo import get_group_by_id, lock_group_currency
from app.repositories.member_repo import get_active_members, get_membership
from app.repositories.user_repo import get_user_by_id
from app.schemas.expense import ExpenseListItem, ExpenseOut, ExpenseSplitOut, SplitInput
from app.services.group_service import require_active_group, require_active_member


# ── SPLIT CALCULATION ────────────────────────────────────────────

def build_splits(
    split_type: str,
    amount_base: float,
    splits_input: list[SplitInput],
) -> list[dict]:
    """
    Takes split inputs and returns a list of DB-ready dicts:
      [{"user_id": ..., "amount_owed_base": ..., "share_value": ...}, ...]

    Validates that amounts/percentages/shares add up correctly.
    """
    n = len(splits_input)
    if n == 0:
        raise HTTPException(status_code=400, detail="At least one participant is required")

    if split_type == "EQUAL":
        per_person = round(amount_base / n, 2)
        return [{"user_id": s.user_id, "amount_owed_base": per_person, "share_value": None}
                for s in splits_input]

    elif split_type == "UNEQUAL":
        total = sum(s.value for s in splits_input)
        if abs(total - amount_base) > 0.02:
            raise HTTPException(
                status_code=400,
                detail=f"UNEQUAL split amounts ({round(total,2)}) must add up to the total ({round(amount_base,2)})"
            )
        return [{"user_id": s.user_id, "amount_owed_base": round(s.value, 2), "share_value": None}
                for s in splits_input]

    elif split_type == "PERCENTAGE":
        total_pct = sum(s.value for s in splits_input)
        if abs(total_pct - 100) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"PERCENTAGE splits must add up to 100% (got {round(total_pct,2)}%)"
            )
        return [
            {
                "user_id": s.user_id,
                "amount_owed_base": round(amount_base * s.value / 100, 2),
                "share_value": s.value,
            }
            for s in splits_input
        ]

    elif split_type == "SHARE":
        total_shares = sum(s.value for s in splits_input)
        if total_shares <= 0:
            raise HTTPException(status_code=400, detail="Total shares must be greater than zero")
        return [
            {
                "user_id": s.user_id,
                "amount_owed_base": round(amount_base * s.value / total_shares, 2),
                "share_value": s.value,
            }
            for s in splits_input
        ]

    raise HTTPException(status_code=400, detail="Invalid split type")


# ── HELPER ───────────────────────────────────────────────────────

async def build_expense_out(db: AsyncSession, expense, splits) -> ExpenseOut:
    """Builds an ExpenseOut response from an expense and its splits."""
    payer = await get_user_by_id(db, str(expense.paid_by_user_id))
    payer_name = payer.display_name if payer else "Unknown"

    split_out_list = []
    for split in splits:
        user = await get_user_by_id(db, str(split.user_id))
        split_out_list.append(ExpenseSplitOut(
            user_id=split.user_id,
            display_name=user.display_name if user else "Unknown",
            amount_owed_base=float(split.amount_owed_base),
        ))

    return ExpenseOut(
        id=expense.id,
        group_id=expense.group_id,
        description=expense.description,
        notes=expense.notes,
        paid_by_user_id=expense.paid_by_user_id,
        paid_by_name=payer_name,
        amount_original=float(expense.amount_original),
        currency_original=expense.currency_original,
        amount_base=float(expense.amount_base),
        fx_rate_used=float(expense.fx_rate_used) if expense.fx_rate_used else None,
        split_type=expense.split_type.value,
        expense_date=expense.expense_date,
        splits=split_out_list,
        created_at=expense.created_at,
    )


# ── SERVICES ─────────────────────────────────────────────────────

async def create_new_expense(
    db: AsyncSession,
    group_id: UUID,
    current_user: User,
    description: str,
    notes: str | None,
    amount: float,
    currency: str,
    split_type: str,
    expense_date,
    paid_by_user_id: UUID,
    splits_input: list[SplitInput],
) -> ExpenseOut:
    """
    Creates an expense with calculated splits.

    Steps:
    1. Validate group is active and user is a member
    2. Get FX rate (if currency != base currency)
    3. Lock group currency if this is the first expense
    4. If no splits provided (EQUAL only): use all active members
    5. Calculate split amounts
    6. Save expense + splits
    """
    # Step 1: Validate
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await require_active_group(group)
    await require_active_member(db, group_id, current_user.id)

    # Step 2: Get FX rate
    fx_rate = await get_exchange_rate(currency, group.base_currency)
    amount_base = round(amount * fx_rate, 2)

    # Step 3: Lock currency after first expense
    if not group.currency_locked:
        await lock_group_currency(db, group)

    # Step 4: If EQUAL and no splits provided → use all active members
    if split_type == "EQUAL" and not splits_input:
        active_members = await get_active_members(db, group_id)
        splits_input = [SplitInput(user_id=m.user_id) for m in active_members]

    # Step 5: Calculate splits
    splits_data = build_splits(split_type, amount_base, splits_input)

    # Step 6: Save to DB
    expense = await create_expense(
        db,
        group_id=group_id,
        paid_by_user_id=paid_by_user_id,
        description=description,
        notes=notes,
        amount_original=amount,
        currency_original=currency,
        amount_base=amount_base,
        fx_rate_used=fx_rate if fx_rate != 1.0 else None,
        expense_date=expense_date,
        split_type=SplitType(split_type),
        created_by_user_id=current_user.id,
    )
    await create_splits(db, expense.id, splits_data)

    splits = await get_expense_splits(db, expense.id)
    return await build_expense_out(db, expense, splits)


async def list_group_expenses(
    db: AsyncSession,
    group_id: UUID,
    current_user: User,
) -> list[ExpenseListItem]:
    """Returns a summary list of all expenses in a group."""
    await require_active_member(db, group_id, current_user.id)

    expenses = await get_group_expenses(db, group_id)

    result = []
    for expense in expenses:
        payer = await get_user_by_id(db, str(expense.paid_by_user_id))
        result.append(ExpenseListItem(
            id=expense.id,
            description=expense.description,
            paid_by_user_id=expense.paid_by_user_id,
            paid_by_name=payer.display_name if payer else "Unknown",
            amount_original=float(expense.amount_original),
            currency_original=expense.currency_original,
            amount_base=float(expense.amount_base),
            split_type=expense.split_type.value,
            expense_date=expense.expense_date,
            created_at=expense.created_at,
        ))
    return result


async def get_expense_detail(
    db: AsyncSession,
    group_id: UUID,
    expense_id: UUID,
    current_user: User,
) -> ExpenseOut:
    """Returns full expense detail including all splits."""
    await require_active_member(db, group_id, current_user.id)

    expense = await get_expense_by_id(db, expense_id)
    if not expense or expense.group_id != group_id:
        raise HTTPException(status_code=404, detail="Expense not found")

    splits = await get_expense_splits(db, expense_id)
    return await build_expense_out(db, expense, splits)


async def update_expense(
    db: AsyncSession,
    group_id: UUID,
    expense_id: UUID,
    current_user: User,
    description: str | None,
    notes: str | None,
    expense_date,
) -> ExpenseOut:
    """
    Updates an expense's description, notes, or date.
    Only the payer or a group admin can edit an expense.
    """
    await require_active_member(db, group_id, current_user.id)

    expense = await get_expense_by_id(db, expense_id)
    if not expense or expense.group_id != group_id:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Check permission: must be payer or admin
    membership = await get_membership(db, group_id, current_user.id)
    is_admin = membership and membership.role == MemberRole.ADMIN
    is_payer = expense.paid_by_user_id == current_user.id

    if not is_admin and not is_payer:
        raise HTTPException(
            status_code=403,
            detail="Only the person who paid or a group admin can edit this expense"
        )

    if description is not None:
        expense.description = description
    if notes is not None:
        expense.notes = notes
    if expense_date is not None:
        expense.expense_date = expense_date

    await db.commit()
    await db.refresh(expense)

    splits = await get_expense_splits(db, expense_id)
    return await build_expense_out(db, expense, splits)


async def delete_expense(
    db: AsyncSession,
    group_id: UUID,
    expense_id: UUID,
    current_user: User,
) -> dict:
    """
    Soft-deletes an expense. Only the payer or a group admin can delete.
    """
    await require_active_member(db, group_id, current_user.id)

    expense = await get_expense_by_id(db, expense_id)
    if not expense or expense.group_id != group_id:
        raise HTTPException(status_code=404, detail="Expense not found")

    membership = await get_membership(db, group_id, current_user.id)
    is_admin = membership and membership.role == MemberRole.ADMIN
    is_payer = expense.paid_by_user_id == current_user.id

    if not is_admin and not is_payer:
        raise HTTPException(
            status_code=403,
            detail="Only the person who paid or a group admin can delete this expense"
        )

    await soft_delete_expense(db, expense)
    return {"message": "Expense deleted successfully"}
