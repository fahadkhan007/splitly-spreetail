# app/services/settlement_service.py

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.fx import get_exchange_rate
from app.models.settlement import SettlementStatus
from app.models.group_member import MemberRole
from app.models.user import User
from app.repositories.group_repo import get_group_by_id
from app.repositories.member_repo import get_membership
from app.repositories.settlement_repo import (
    create_settlement,
    get_settlement_by_id,
    get_group_settlements,
    void_settlement,
)
from app.repositories.user_repo import get_user_by_id
from app.schemas.settlement import SettlementOut
from app.services.group_service import require_active_group, require_active_member


async def build_settlement_out(db: AsyncSession, settlement) -> SettlementOut:
    payer = await get_user_by_id(db, str(settlement.payer_user_id))
    payee = await get_user_by_id(db, str(settlement.payee_user_id))
    return SettlementOut(
        id=settlement.id,
        group_id=settlement.group_id,
        payer_user_id=settlement.payer_user_id,
        payer_name=payer.display_name if payer else "Unknown",
        payee_user_id=settlement.payee_user_id,
        payee_name=payee.display_name if payee else "Unknown",
        amount_original=float(settlement.amount_original),
        currency_original=settlement.currency_original,
        amount_base=float(settlement.amount_base),
        fx_rate_used=float(settlement.fx_rate_used) if settlement.fx_rate_used else None,
        settlement_date=settlement.settlement_date,
        status=settlement.status.value,
        notes=settlement.notes,
        created_at=settlement.created_at,
    )


async def create_new_settlement(
    db: AsyncSession,
    group_id: UUID,
    current_user: User,
    payer_user_id: UUID,
    payee_user_id: UUID,
    amount: float,
    currency: str,
    notes: str | None,
    settlement_date,
) -> SettlementOut:
    """
    Records a payment from payer to payee.
    Any active group member can record a settlement.
    """
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await require_active_group(group)
    await require_active_member(db, group_id, current_user.id)

    if payer_user_id == payee_user_id:
        raise HTTPException(status_code=400, detail="Payer and payee cannot be the same person")

    # Get FX rate
    fx_rate = await get_exchange_rate(currency, group.base_currency)
    amount_base = round(amount * fx_rate, 2)

    settlement = await create_settlement(
        db,
        group_id=group_id,
        payer_user_id=payer_user_id,
        payee_user_id=payee_user_id,
        amount_original=amount,
        currency_original=currency,
        amount_base=amount_base,
        fx_rate_used=fx_rate if fx_rate != 1.0 else None,
        settlement_date=settlement_date,
        status=SettlementStatus.ACTIVE,
        notes=notes,
        recorded_by_user_id=current_user.id,
    )
    return await build_settlement_out(db, settlement)


async def list_settlements(
    db: AsyncSession,
    group_id: UUID,
    current_user: User,
) -> list[SettlementOut]:
    """Lists all settlements (ACTIVE and VOIDED) for a group."""
    await require_active_member(db, group_id, current_user.id)
    settlements = await get_group_settlements(db, group_id)
    return [await build_settlement_out(db, s) for s in settlements]


async def void_group_settlement(
    db: AsyncSession,
    group_id: UUID,
    settlement_id: UUID,
    current_user: User,
) -> SettlementOut:
    """
    Voids a settlement. Only the person who recorded it or a group admin can void it.
    Voided settlements are ignored in balance calculations but NOT deleted.
    """
    await require_active_member(db, group_id, current_user.id)

    settlement = await get_settlement_by_id(db, settlement_id)
    if not settlement or settlement.group_id != group_id:
        raise HTTPException(status_code=404, detail="Settlement not found")

    if settlement.status == SettlementStatus.VOIDED:
        raise HTTPException(status_code=400, detail="Settlement is already voided")

    # Only the recorder or an admin can void
    membership = await get_membership(db, group_id, current_user.id)
    is_admin = membership and membership.role == MemberRole.ADMIN
    is_recorder = settlement.recorded_by_user_id == current_user.id

    if not is_admin and not is_recorder:
        raise HTTPException(
            status_code=403,
            detail="Only the person who recorded this settlement or a group admin can void it"
        )

    settlement = await void_settlement(db, settlement, current_user.id)
    return await build_settlement_out(db, settlement)
