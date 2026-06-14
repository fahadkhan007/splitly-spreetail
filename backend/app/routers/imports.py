# app/routers/imports.py
#
# Routes:
#   POST /groups/{group_id}/import          — upload CSV and import expenses
#   GET  /groups/{group_id}/imports         — list past import reports
#   GET  /groups/{group_id}/imports/{id}    — get full import report detail

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.import_schema import ImportReportOut, ImportSummaryOut
from app.services.import_service import (
    get_import_report_detail,
    import_csv_expenses,
    list_import_reports,
)

router = APIRouter()


@router.post("/groups/{group_id}/import", response_model=ImportReportOut, status_code=201)
async def upload_csv(
    group_id: UUID,
    file: UploadFile = File(..., description="CSV file with expense data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a CSV file to import expenses into the group. Admin only.

    Expected CSV columns:
      date, description, amount, currency (optional), paid_by,
      split_among (optional), notes (optional)

    Returns a detailed report of what was imported, skipped, or flagged.
    """
    return await import_csv_expenses(db, group_id, current_user, file)


@router.get("/groups/{group_id}/imports", response_model=list[ImportSummaryOut])
async def list_imports(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists all past CSV imports for this group."""
    return await list_import_reports(db, group_id, current_user.id)


@router.get("/groups/{group_id}/imports/{import_id}", response_model=ImportReportOut)
async def get_import_detail(
    group_id: UUID,
    import_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the full row-by-row detail of a past CSV import."""
    return await get_import_report_detail(db, group_id, import_id)
