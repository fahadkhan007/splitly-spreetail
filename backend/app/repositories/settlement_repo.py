# app/repositories/settlement_repo.py

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settlement import Settlement, SettlementStatus


async def create_settlement(db: AsyncSession, **kwargs) -> Settlement:
    settlement = Settlement(**kwargs)
    db.add(settlement)
    await db.commit()
    await db.refresh(settlement)
    return settlement


async def get_settlement_by_id(db: AsyncSession, settlement_id: UUID) -> Settlement | None:
    result = await db.execute(
        select(Settlement).where(Settlement.id == settlement_id)
    )
    return result.scalar_one_or_none()


async def get_group_settlements(db: AsyncSession, group_id: UUID) -> list[Settlement]:
    """Returns all settlements for a group (ACTIVE and VOIDED), newest first."""
    result = await db.execute(
        select(Settlement)
        .where(Settlement.group_id == group_id)
        .order_by(Settlement.settlement_date.desc(), Settlement.created_at.desc())
    )
    return list(result.scalars().all())


async def get_active_group_settlements(db: AsyncSession, group_id: UUID) -> list[Settlement]:
    """Returns only ACTIVE settlements. Used in balance calculation."""
    result = await db.execute(
        select(Settlement).where(
            Settlement.group_id == group_id,
            Settlement.status == SettlementStatus.ACTIVE,
        )
    )
    return list(result.scalars().all())


async def void_settlement(
    db: AsyncSession,
    settlement: Settlement,
    voided_by_user_id: UUID,
) -> Settlement:
    """Voids a settlement. Original record is preserved, status changes to VOIDED."""
    settlement.status = SettlementStatus.VOIDED
    settlement.voided_by_user_id = voided_by_user_id
    settlement.voided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(settlement)
    return settlement
