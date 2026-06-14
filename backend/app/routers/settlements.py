# app/routers/settlements.py
#
# Routes:
#   POST   /groups/{group_id}/settlements                         — record settlement
#   GET    /groups/{group_id}/settlements                         — list settlements
#   POST   /groups/{group_id}/settlements/{settlement_id}/void    — void a settlement

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.settlement import SettlementCreate, SettlementOut
from app.services.settlement_service import (
    create_new_settlement,
    list_settlements,
    void_group_settlement,
)

router = APIRouter()


@router.post("/groups/{group_id}/settlements", response_model=SettlementOut, status_code=201)
async def record_settlement(
    group_id: UUID,
    body: SettlementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Records a payment between two group members.
    Any active member can record a settlement.
    """
    return await create_new_settlement(
        db,
        group_id=group_id,
        current_user=current_user,
        payer_user_id=body.payer_user_id,
        payee_user_id=body.payee_user_id,
        amount=body.amount,
        currency=body.currency,
        notes=body.notes,
        settlement_date=body.settlement_date,
    )


@router.get("/groups/{group_id}/settlements", response_model=list[SettlementOut])
async def get_settlements(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all settlements for the group (including VOIDED ones)."""
    return await list_settlements(db, group_id, current_user)


@router.post("/groups/{group_id}/settlements/{settlement_id}/void", response_model=SettlementOut)
async def void_settlement(
    group_id: UUID,
    settlement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Voids a settlement — it is no longer counted in balance calculations.
    The record is never deleted. Only the recorder or a group admin can void.
    """
    return await void_group_settlement(db, group_id, settlement_id, current_user)
