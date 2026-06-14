# app/routers/expenses.py
#
# Routes:
#   POST   /groups/{group_id}/expenses                       — add expense
#   GET    /groups/{group_id}/expenses                       — list expenses
#   GET    /groups/{group_id}/expenses/{expense_id}          — get detail
#   PATCH  /groups/{group_id}/expenses/{expense_id}          — edit expense
#   DELETE /groups/{group_id}/expenses/{expense_id}          — soft delete

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.expense import ExpenseCreate, ExpenseListItem, ExpenseOut, ExpenseUpdate
from app.services.expense_service import (
    create_new_expense,
    delete_expense,
    get_expense_detail,
    list_group_expenses,
    update_expense,
)
from app.services.balance_service import get_group_balances
from app.schemas.balance import GroupBalances

router = APIRouter()


@router.post("/groups/{group_id}/expenses", response_model=ExpenseOut, status_code=201)
async def add_expense(
    group_id: UUID,
    body: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Adds a new expense to the group.
    Any active member can add expenses.
    """
    return await create_new_expense(
        db,
        group_id=group_id,
        current_user=current_user,
        description=body.description,
        notes=body.notes,
        amount=body.amount,
        currency=body.currency,
        split_type=body.split_type,
        expense_date=body.expense_date,
        paid_by_user_id=body.paid_by_user_id,
        splits_input=body.splits,
    )


@router.get("/groups/{group_id}/expenses", response_model=list[ExpenseListItem])
async def list_expenses(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all expenses in a group, newest first."""
    return await list_group_expenses(db, group_id, current_user)


@router.get("/groups/{group_id}/expenses/{expense_id}", response_model=ExpenseOut)
async def get_expense(
    group_id: UUID,
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns full expense detail with all split amounts."""
    return await get_expense_detail(db, group_id, expense_id, current_user)


@router.patch("/groups/{group_id}/expenses/{expense_id}", response_model=ExpenseOut)
async def edit_expense(
    group_id: UUID,
    expense_id: UUID,
    body: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates an expense's description, notes, or date. Payer or admin only."""
    return await update_expense(
        db, group_id, expense_id, current_user,
        description=body.description,
        notes=body.notes,
        expense_date=body.expense_date,
    )


@router.delete("/groups/{group_id}/expenses/{expense_id}", response_model=MessageResponse)
async def remove_expense(
    group_id: UUID,
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deletes an expense. Payer or admin only."""
    return await delete_expense(db, group_id, expense_id, current_user)


@router.get("/groups/{group_id}/balances", response_model=GroupBalances)
async def get_balances(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the current balance for every member of the group,
    plus a simplified list of who should pay whom to settle all debts.
    Calculated dynamically — nothing is stored in the database.
    """
    return await get_group_balances(db, group_id, current_user.id)
