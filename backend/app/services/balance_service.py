# app/services/balance_service.py
#
# Calculates group balances dynamically from expenses and settlements.
# Nothing is stored in the database — all balances are computed on the fly.
#
# Formula per user:
#   net = (total paid as payer) - (total owed in splits) + (settlements sent) - (settlements received)
#
#   Positive net → others owe this person
#   Negative net → this person owes others

from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.expense_repo import get_all_expenses_with_splits
from app.repositories.group_repo import get_group_by_id
from app.repositories.member_repo import get_active_members_with_users
from app.repositories.settlement_repo import get_active_group_settlements
from app.schemas.balance import DebtItem, GroupBalances, UserBalance


def simplify_debts(
    balances: dict[str, float],
    user_names: dict[str, str],
) -> list[DebtItem]:
    """
    Greedy debt simplification algorithm.
    Matches the biggest debtor with the biggest creditor repeatedly
    until all debts are settled with the minimum number of transactions.
    """
    creditors = [(uid, bal) for uid, bal in balances.items() if bal > 0.01]
    debtors = [(uid, -bal) for uid, bal in balances.items() if bal < -0.01]

    creditors.sort(key=lambda x: -x[1])
    debtors.sort(key=lambda x: -x[1])

    creditors = [list(c) for c in creditors]
    debtors = [list(d) for d in debtors]

    transactions = []
    i, j = 0, 0

    while i < len(creditors) and j < len(debtors):
        creditor_id, credit_amount = creditors[i]
        debtor_id, debt_amount = debtors[j]

        payment = min(credit_amount, debt_amount)
        transactions.append(DebtItem(
            from_user_id=UUID(debtor_id),
            from_name=user_names.get(debtor_id, "Unknown"),
            to_user_id=UUID(creditor_id),
            to_name=user_names.get(creditor_id, "Unknown"),
            amount=round(payment, 2),
        ))

        creditors[i][1] -= payment
        debtors[j][1] -= payment

        if creditors[i][1] < 0.01:
            i += 1
        if debtors[j][1] < 0.01:
            j += 1

    return transactions


async def get_group_balances(
    db: AsyncSession,
    group_id: UUID,
    current_user_id: UUID,
) -> GroupBalances:
    """
    Calculates and returns the balance for every member in the group.

    Returns:
    - balances: each member's net balance (+ = owed, - = owes)
    - simplified_debts: the minimal list of payments to settle all debts
    """
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # ── COLLECT ALL USER IDs AND NAMES ───────────────────────────
    # Start with current active members
    member_rows = await get_active_members_with_users(db, group_id)
    user_names: dict[str, str] = {}
    for _, user in member_rows:
        user_names[str(user.id)] = user.display_name

    # ── INITIALIZE BALANCES ──────────────────────────────────────
    # defaultdict so any user_id encountered in splits is included automatically
    net: dict[str, float] = defaultdict(float)

    # ── PROCESS EXPENSES ─────────────────────────────────────────
    # For each expense: payer gets credited, split participants get debited
    expense_rows = await get_all_expenses_with_splits(db, group_id)
    for expense, split in expense_rows:
        # Credit the payer with the full expense amount
        net[str(expense.paid_by_user_id)] += float(expense.amount_base)
        # Debit each participant their share
        net[str(split.user_id)] -= float(split.amount_owed_base)

    # ── PROCESS SETTLEMENTS ──────────────────────────────────────
    # Settlements reduce what debtors owe to creditors
    settlements = await get_active_group_settlements(db, group_id)
    for s in settlements:
        # Payer "gave" money → reduce their debt (or increase their credit)
        net[str(s.payer_user_id)] += float(s.amount_base)
        # Payee "received" money → reduce their credit (or increase their debt)
        net[str(s.payee_user_id)] -= float(s.amount_base)

    # ── BUILD RESPONSE ───────────────────────────────────────────
    # Only include users who appear in at least one expense or settlement
    balance_list = []
    for user_id_str, balance in net.items():
        # Round tiny floating-point residuals to zero
        balance = round(balance, 2)
        balance_list.append(UserBalance(
            user_id=UUID(user_id_str),
            display_name=user_names.get(user_id_str, "Unknown"),
            net_balance=balance,
        ))

    # Sort: biggest creditors first, biggest debtors last
    balance_list.sort(key=lambda b: -b.net_balance)

    # Build simplified debt list
    simplified = simplify_debts(
        {str(b.user_id): b.net_balance for b in balance_list},
        user_names,
    )

    return GroupBalances(
        group_id=group_id,
        base_currency=group.base_currency,
        balances=balance_list,
        simplified_debts=simplified,
    )
