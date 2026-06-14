# app/routers/reports.py
#
# Routes:
#   GET /groups/{group_id}/reports/summary   — overall group summary
#   GET /groups/{group_id}/reports/monthly   — expenses broken down by month

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.report import GroupSummaryReport, MonthlyReport
from app.services.report_service import get_monthly_report, get_summary_report

router = APIRouter()


@router.get("/groups/{group_id}/reports/summary", response_model=GroupSummaryReport)
async def summary_report(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a complete summary of the group:
    - Total expenses and amount
    - Breakdown by category
    - Each member's total paid, total owed, and net balance
    """
    return await get_summary_report(db, group_id, current_user.id)


@router.get("/groups/{group_id}/reports/monthly", response_model=MonthlyReport)
async def monthly_report(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns expense totals grouped by month (newest first).
    Useful for tracking spending trends over time.
    """
    return await get_monthly_report(db, group_id, current_user.id)
