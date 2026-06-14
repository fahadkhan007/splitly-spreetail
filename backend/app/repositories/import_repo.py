# app/repositories/import_repo.py

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.import_report import ImportReport
from app.models.import_report_item import ImportReportItem, ImportOutcome, AnomalySeverity


async def create_import_report(db: AsyncSession, **kwargs) -> ImportReport:
    report = ImportReport(**kwargs)
    db.add(report)
    await db.flush()   # get the ID before committing
    return report


async def create_import_report_item(db: AsyncSession, **kwargs) -> ImportReportItem:
    item = ImportReportItem(**kwargs)
    db.add(item)
    return item


async def finalize_import_report(
    db: AsyncSession,
    report: ImportReport,
    total_rows: int,
    imported: int,
    skipped: int,
    warnings: int,
    errors: int,
    summary: str,
) -> ImportReport:
    """Updates the import report with final counts and commits everything."""
    report.total_rows_processed = total_rows
    report.rows_successfully_imported = imported
    report.rows_skipped = skipped
    report.warning_count = warnings
    report.error_count = errors
    report.final_summary = summary
    await db.commit()
    await db.refresh(report)
    return report


async def get_group_import_reports(db: AsyncSession, group_id: UUID) -> list[ImportReport]:
    result = await db.execute(
        select(ImportReport)
        .where(ImportReport.group_id == group_id)
        .order_by(ImportReport.created_at.desc())
    )
    return list(result.scalars().all())


async def get_import_report_by_id(db: AsyncSession, import_id: UUID) -> ImportReport | None:
    result = await db.execute(
        select(ImportReport).where(ImportReport.id == import_id)
    )
    return result.scalar_one_or_none()


async def get_import_report_items(db: AsyncSession, import_id: UUID) -> list[ImportReportItem]:
    result = await db.execute(
        select(ImportReportItem)
        .where(ImportReportItem.import_id == import_id)
        .order_by(ImportReportItem.row_number)
    )
    return list(result.scalars().all())
