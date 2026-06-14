# app/schemas/import_schema.py

from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel


class ImportRowResult(BaseModel):
    """Result for one CSV row — shown in the import report."""
    row_number: int
    outcome: str                # "IMPORTED", "SKIPPED", "CONVERTED"
    anomalies: list[str]        # List of issue descriptions for this row
    raw_data: dict[str, Any]    # The original CSV row as a dict


class ImportReportOut(BaseModel):
    import_id: UUID
    group_id: UUID
    filename: str
    total_rows: int
    imported: int
    skipped: int
    converted: int           # imported but currency was converted
    warning_count: int
    error_count: int
    rows: list[ImportRowResult]
    created_at: datetime


class ImportSummaryOut(BaseModel):
    """Compact import summary for the list view."""
    import_id: UUID
    filename: str
    total_rows: int
    imported: int
    skipped: int
    warning_count: int
    error_count: int
    created_at: datetime
