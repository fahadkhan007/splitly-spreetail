# app/models/__init__.py
#
# This file imports every model so that:
#   1. Alembic can detect all tables during migration generation
#   2. Any file that does `from app.models import User` works cleanly
#
# Import order matters: tables that are referenced by FKs in other tables
# must be imported first so SQLAlchemy can resolve the foreign key references.

from app.models.user import User, UserStatus
from app.models.import_report import ImportReport           # imported early (referenced by expenses + settlements)
from app.models.group import Group, GroupStatus
from app.models.group_member import GroupMember, MemberRole
from app.models.invitation import Invitation, InvitationStatus
from app.models.expense import Expense, SplitType
from app.models.expense_split import ExpenseSplit
from app.models.settlement import Settlement, SettlementStatus
from app.models.import_report_item import ImportReportItem, AnomalySeverity, ImportOutcome

__all__ = [
    "User", "UserStatus",
    "ImportReport",
    "Group", "GroupStatus",
    "GroupMember", "MemberRole",
    "Invitation", "InvitationStatus",
    "Expense", "SplitType",
    "ExpenseSplit",
    "Settlement", "SettlementStatus",
    "ImportReportItem", "AnomalySeverity", "ImportOutcome",
]
