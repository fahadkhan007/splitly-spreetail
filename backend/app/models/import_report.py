# app/models/import_report.py
#
# ImportReport stores a summary of each CSV import session.
# One record is created per import, regardless of how many rows were in the CSV.
#
# We define this model early because expenses and settlements both reference it
# (they store which import session created them, for traceability).

import uuid

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class ImportReport(Base):
    __tablename__ = "import_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which group this import was for
    group_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Which admin triggered the import
    initiated_by_user_id = Column(UUID(as_uuid=True), nullable=False)

    # Original filename of the uploaded CSV
    csv_filename = Column(String(255), nullable=False)

    # Row counts — filled in after the import finishes
    total_rows_processed = Column(Integer, nullable=False, default=0)
    rows_successfully_imported = Column(Integer, nullable=False, default=0)
    rows_skipped = Column(Integer, nullable=False, default=0)

    # Count of anomalies found during this import
    warning_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)

    # A human-readable summary shown to the user after import completes
    final_summary = Column(Text, nullable=True)

    # created_at = the timestamp of when the import happened
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
