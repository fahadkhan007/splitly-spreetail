# app/repositories/expense_repo.py
#
# Database queries for expenses and their splits.

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit


async def create_expense(db: AsyncSession, **kwargs) -> Expense:
    """Creates an expense record. Caller must add splits separately and commit."""
    expense = Expense(**kwargs)
    db.add(expense)
    await db.flush()  # flush to get the generated UUID without committing yet
    return expense


async def create_splits(db: AsyncSession, expense_id: UUID, splits_data: list[dict]) -> None:
    """
    Creates all expense split records for a given expense.
    splits_data is a list of dicts with keys: user_id, amount_owed_base, share_value (optional)
    """
    for item in splits_data:
        db.add(ExpenseSplit(
            expense_id=expense_id,
            user_id=item["user_id"],
            amount_owed_base=item["amount_owed_base"],
            share_value=item.get("share_value"),
        ))
    await db.commit()


async def get_expense_by_id(db: AsyncSession, expense_id: UUID) -> Expense | None:
    """Finds a non-deleted expense by ID."""
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.is_deleted == False)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def get_group_expenses(db: AsyncSession, group_id: UUID) -> list[Expense]:
    """Returns all non-deleted expenses for a group, newest first."""
    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id, Expense.is_deleted == False)  # noqa: E712
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
    )
    return list(result.scalars().all())


async def get_expense_splits(db: AsyncSession, expense_id: UUID) -> list[ExpenseSplit]:
    """Returns all splits for a given expense."""
    result = await db.execute(
        select(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id)
    )
    return list(result.scalars().all())


async def delete_splits_for_expense(db: AsyncSession, expense_id: UUID) -> None:
    """Deletes all split records for an expense (used before recreating splits on edit)."""
    await db.execute(delete(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id))


async def soft_delete_expense(db: AsyncSession, expense: Expense) -> Expense:
    """Marks the expense as deleted. Splits are kept for audit purposes."""
    expense.is_deleted = True
    await db.commit()
    return expense


async def get_all_expenses_with_splits(db: AsyncSession, group_id: UUID):
    """
    Returns all non-deleted expenses for a group joined with their splits.
    Used for balance calculation — returns (Expense, ExpenseSplit) row pairs.
    """
    result = await db.execute(
        select(Expense, ExpenseSplit)
        .join(ExpenseSplit, Expense.id == ExpenseSplit.expense_id)
        .where(Expense.group_id == group_id, Expense.is_deleted == False)  # noqa: E712
    )
    return list(result.all())
