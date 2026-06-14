# app/models/import_report_item.py
#
# ImportReportItem stores one row for each anomaly or transformation
# that happened during a CSV import.
#
# Every time the system:
#   - detects an anomaly
#   - auto-corrects something (like normalizing "priya" to "Priya")
#   - skips a row
#   - successfully imports a row
# ...it writes one ImportReportItem record.
#
# This gives the user (and auditors) a complete trace of what the system did.

import enum
import uuid

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.database import Base


class AnomalySeverity(str, enum.Enum):
    HIGH = "HIGH"       # Must be resolved by user before import can proceed
    MEDIUM = "MEDIUM"   # Auto-resolved with a suggested fix, user can override
    LOW = "LOW"         # Auto-resolved silently (e.g. name casing), logged here
    INFO = "INFO"       # Informational note only, no action needed


class ImportOutcome(str, enum.Enum):
    IMPORTED = "IMPORTED"   # Row was successfully imported
    SKIPPED = "SKIPPED"     # Row was skipped (user chose to skip or it was unresolvable)
    CONVERTED = "CONVERTED" # Row was imported after a transformation (e.g. currency conversion)


class ImportReportItem(Base):
    __tablename__ = "import_report_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which import session this item belongs to
    import_id = Column(UUID(as_uuid=True), ForeignKey("import_reports.id"), nullable=False, index=True)

    # The row number in the original CSV file (for the user to find the row easily)
    row_number = Column(Integer, nullable=False)

    # The category of anomaly found (e.g. 'PROBABLE_DUPLICATE', 'MISSING_PAYER')
    # NULL if the row had no anomaly and was imported cleanly
    anomaly_type = Column(String(100), nullable=True)

    severity = Column(Enum(AnomalySeverity), nullable=True)

    # A snapshot of the original CSV row as it appeared before any changes.
    # Stored as JSON so the user can see exactly what was in the file.
    raw_data = Column(JSONB, nullable=False)

    # What the user chose to do with this anomaly (e.g. "Keep row 5", "Skip row")
    resolution_chosen = Column(String(200), nullable=True)

    # Description of any automatic transformation that was applied
    # (e.g. "Stripped comma from '1,200' → '1200.00'")
    transformation_applied = Column(Text, nullable=True)

    # If a currency conversion happened for this row, store the rate used
    fx_rate_used = Column(Numeric(18, 6), nullable=True)

    # Final result for this row
    outcome = Column(Enum(ImportOutcome), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
