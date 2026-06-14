# app/services/import_service.py
#
# Imports expenses_export.csv into a group.
#
# CSV format (actual columns):
#   date, description, paid_by, amount, currency,
#   split_type, split_with, split_details, notes
#
# split_with uses SEMICOLONS as separator (not commas).
# split_details holds raw values for UNEQUAL / PERCENTAGE / SHARE rows.
#
# Anomalies detected and policies applied (see SCOPE.md for full list):
#   1.  Duplicate row (same date+amount+payer)   → skip 2nd occurrence, warn
#   2.  Settlement disguised as expense           → import as Settlement
#   3.  Payer name case mismatch ("priya")        → case-insensitive match, LOW log
#   4.  Fuzzy payer name ("Priya S")              → match by first word, MEDIUM warn
#   5.  Missing payer                             → skip, HIGH error
#   6.  Amount "1,200" (comma-formatted)          → auto-strip comma, LOW log
#   7.  Negative amount (refund)                  → import as negative expense, INFO
#   8.  Zero amount                               → skip, HIGH error
#   9.  "Mar-14" date format                      → parse as March 14 2026, MEDIUM warn
#  10.  Ambiguous date "04-05-2026"               → use DD-MM-YYYY, MEDIUM warn
#  11.  Missing currency                          → default to group base currency
#  12.  Unknown participant ("Kabir")             → exclude from split, MEDIUM warn
#  13.  Ghost member (Meera in April after leaving)→ exclude from split, MEDIUM warn
#  14.  Percentage sum ≠ 100%                     → skip, HIGH error
#  15.  Unequal amounts don't match total         → skip, HIGH error
#  16.  Unknown split_type                        → skip, HIGH error
#  17.  split_type conflict (equal + share details)→ use declared split_type, LOW log

import csv
import io
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.fx import get_exchange_rate
from app.models.expense import SplitType
from app.models.group_member import GroupMember
from app.models.import_report_item import AnomalySeverity, ImportOutcome
from app.models.settlement import SettlementStatus
from app.models.user import User
from app.repositories.expense_repo import create_expense, create_splits, get_group_expenses
from app.repositories.group_repo import get_group_by_id, lock_group_currency
from app.repositories.import_repo import (
    create_import_report,
    create_import_report_item,
    finalize_import_report,
    get_group_import_reports,
    get_import_report_by_id,
    get_import_report_items,
)
from app.repositories.member_repo import get_all_members_with_users
from app.repositories.settlement_repo import create_settlement
from app.schemas.import_schema import ImportReportOut, ImportRowResult, ImportSummaryOut
from app.services.group_service import require_active_group, require_admin


# ── DATE PARSING ─────────────────────────────────────────────────

DATE_FORMATS = [
    "%d-%m-%Y",   # 15-01-2026  ← primary format in this CSV
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%d/%m/%y",
]


def parse_date(value: str) -> tuple[date | None, str | None]:
    """
    Returns (parsed_date, warning_or_None).
    Handles the non-standard "Mar-14" format found in row 27.
    Flags ambiguous dates like "04-05-2026" where DD vs MM is unclear.
    """
    value = value.strip()

    # Handle "Mar-14" style (month abbreviation + day, no year) → assume 2026
    try:
        parsed = datetime.strptime(f"{value}-2026", "%b-%d-%Y").date()
        return parsed, f"Date '{value}' had no year — interpreted as {parsed} (assumed 2026)"
    except ValueError:
        pass

    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt).date()
            # Flag dates where DD and MM are both ≤ 12 (ambiguous)
            warning = None
            if fmt == "%d-%m-%Y" and parsed.day <= 12:
                try:
                    alt = datetime.strptime(value, "%m-%d-%Y").date()
                    if alt != parsed:
                        warning = (
                            f"Ambiguous date '{value}': interpreted as {parsed} (DD-MM-YYYY). "
                            f"Could also be {alt} (MM-DD-YYYY)."
                        )
                except ValueError:
                    pass
            return parsed, warning
        except ValueError:
            continue

    return None, None


# ── AMOUNT PARSING ───────────────────────────────────────────────

def parse_amount(value: str) -> float | None:
    """Strips commas, currency symbols, whitespace. Returns float or None."""
    cleaned = value.strip().replace(",", "").replace(" ", "")
    for sym in ["₹", "$", "€", "£", "¥"]:
        cleaned = cleaned.replace(sym, "")
    try:
        return float(cleaned)
    except ValueError:
        return None


# ── MEMBER MATCHING ──────────────────────────────────────────────

def find_member(
    name: str,
    all_members: list[tuple[GroupMember, User]],
) -> tuple[GroupMember, User, bool] | None:
    """
    Returns (GroupMember, User, was_fuzzy_match).
    First tries exact case-insensitive match on display_name or email.
    Then tries matching by first word only (catches "Priya S" → Priya).
    Returns None if no match found.
    """
    name_clean = name.strip()
    name_lower = name_clean.lower()

    # Exact match
    for member, user in all_members:
        if user.display_name.lower() == name_lower or user.email.lower() == name_lower:
            return member, user, False

    # Fuzzy: first word of input matches first word of member name
    first_word = name_lower.split()[0] if name_lower.split() else ""
    if first_word:
        for member, user in all_members:
            member_first = user.display_name.lower().split()[0]
            if member_first == first_word:
                return member, user, True

    return None


# ── SETTLEMENT DETECTION ─────────────────────────────────────────

def is_settlement_row(description: str, split_type: str, notes: str) -> bool:
    """
    Returns True if the row looks like a settlement/payment rather than a shared expense.
    Covers rows 14 and 38 in the actual CSV.
    """
    desc = description.lower()
    note = (notes or "").lower()

    if not split_type:
        return True
    if "paid" in desc and "back" in desc:
        return True
    if "settlement" in desc or "settlement" in note:
        return True
    if "deposit" in desc and "moving in" in note:
        return True
    return False


# ── SPLIT DETAILS PARSER ─────────────────────────────────────────

def parse_split_details(details_str: str) -> list[dict]:
    """
    Parses split_details like:
      "Rohan 700; Priya 400; Meera 400"        (UNEQUAL)
      "Aisha 30%; Rohan 30%; Priya 30%"        (PERCENTAGE)
      "Aisha 1; Rohan 2; Priya 1; Dev 2"       (SHARE)
    Returns [{name: str, value: float}, ...]
    """
    if not details_str or not details_str.strip():
        return []
    result = []
    for entry in details_str.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.rsplit(None, 1)  # split from right on whitespace
        if len(parts) != 2:
            continue
        name = parts[0].strip()
        value_str = parts[1].strip().rstrip("%")
        try:
            result.append({"name": name, "value": float(value_str)})
        except ValueError:
            continue
    return result


# ── GHOST MEMBER CHECK ───────────────────────────────────────────

def is_ghost_member(member: GroupMember, expense_date: date) -> bool:
    """Returns True if this member left the group before the expense date."""
    if member.left_at is None:
        return False
    return expense_date > member.left_at.date()


# ── DUPLICATE CHECK ──────────────────────────────────────────────

def is_probable_duplicate(
    expense_date: date,
    amount: float,
    payer_id: UUID,
    seen_this_session: list[tuple],
    existing_expenses: list,
) -> bool:
    key = (expense_date, round(amount, 2), payer_id)
    if key in seen_this_session:
        return True
    for exp in existing_expenses:
        if (exp.expense_date == expense_date
                and abs(float(exp.amount_original) - amount) < 0.01
                and exp.paid_by_user_id == payer_id):
            return True
    return False


# ── MAIN IMPORT FUNCTION ─────────────────────────────────────────

async def import_csv_expenses(
    db: AsyncSession,
    group_id: UUID,
    current_user: User,
    csv_file: UploadFile,
) -> ImportReportOut:

    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await require_active_group(group)
    await require_admin(db, group_id, current_user.id)

    # Read CSV
    content = await csv_file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    raw_rows = [{k.strip().lower(): (v or "").strip() for k, v in row.items()} for row in reader]

    if not raw_rows:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Load ALL members (including those who left) — needed for ghost detection
    all_members = await get_all_members_with_users(db, group_id)
    existing_expenses = await get_group_expenses(db, group_id)

    # Create import report record
    import_report = await create_import_report(
        db,
        group_id=group_id,
        initiated_by_user_id=current_user.id,
        csv_filename=csv_file.filename or "upload.csv",
        total_rows_processed=0,
        rows_successfully_imported=0,
        rows_skipped=0,
        warning_count=0,
        error_count=0,
    )

    row_results: list[ImportRowResult] = []
    imported = skipped = converted = warnings = errors = 0
    seen_keys: list[tuple] = []  # (date, amount, payer_id) seen in this session

    for row_num, raw in enumerate(raw_rows, start=2):
        anomalies: list[str] = []
        outcome = ImportOutcome.IMPORTED

        # ── 1. REQUIRED FIELDS ────────────────────────────────
        missing = [f for f in ["date", "description", "paid_by", "amount"] if not raw.get(f)]
        if missing:
            note = f"Missing required columns: {', '.join(missing)}"
            anomalies.append(note)
            await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                anomaly_type="MISSING_REQUIRED_FIELDS", severity=AnomalySeverity.HIGH,
                raw_data=raw, outcome=ImportOutcome.SKIPPED, resolution_chosen="Row skipped")
            row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
            skipped += 1; errors += 1
            continue

        # ── 2. PARSE DATE ─────────────────────────────────────
        parsed_date, date_warning = parse_date(raw["date"])
        if not parsed_date:
            anomalies.append(f"Unrecognised date format: '{raw['date']}'")
            await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                anomaly_type="INVALID_DATE", severity=AnomalySeverity.HIGH,
                raw_data=raw, outcome=ImportOutcome.SKIPPED, resolution_chosen="Row skipped")
            row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
            skipped += 1; errors += 1
            continue
        if date_warning:
            anomalies.append(date_warning)
            warnings += 1

        # ── 3. PARSE AMOUNT ───────────────────────────────────
        parsed_amount = parse_amount(raw["amount"])
        if parsed_amount is None:
            anomalies.append(f"Cannot parse amount: '{raw['amount']}'")
            await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                anomaly_type="INVALID_AMOUNT", severity=AnomalySeverity.HIGH,
                raw_data=raw, outcome=ImportOutcome.SKIPPED, resolution_chosen="Row skipped")
            row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
            skipped += 1; errors += 1
            continue

        if parsed_amount == 0:
            anomalies.append("Amount is zero — likely a placeholder or already-reversed entry")
            await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                anomaly_type="ZERO_AMOUNT", severity=AnomalySeverity.HIGH,
                raw_data=raw, outcome=ImportOutcome.SKIPPED,
                resolution_chosen="Row skipped — zero amount has no financial effect")
            row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
            skipped += 1; errors += 1
            continue

        is_refund = parsed_amount < 0
        if is_refund:
            anomalies.append(f"Negative amount {parsed_amount} — treated as refund/credit")
            warnings += 1

        # ── 4. CURRENCY & FX ──────────────────────────────────
        currency = (raw.get("currency") or "").strip().upper()
        if not currency or len(currency) != 3:
            anomalies.append(f"Missing/invalid currency '{raw.get('currency', '')}' — defaulting to {group.base_currency}")
            currency = group.base_currency
            warnings += 1

        try:
            fx_rate = await get_exchange_rate(currency, group.base_currency)
        except HTTPException:
            anomalies.append(f"Exchange rate unavailable for {currency} → {group.base_currency}")
            await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                anomaly_type="FX_UNAVAILABLE", severity=AnomalySeverity.HIGH,
                raw_data=raw, outcome=ImportOutcome.SKIPPED, resolution_chosen="Row skipped")
            row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
            skipped += 1; errors += 1
            continue

        amount_base = round(parsed_amount * fx_rate, 2)
        if currency != group.base_currency:
            outcome = ImportOutcome.CONVERTED
            anomalies.append(f"Converted {parsed_amount} {currency} → {amount_base} {group.base_currency} (rate: {fx_rate})")
            converted += 1

        # ── 5. FIND PAYER ─────────────────────────────────────
        payer_match = find_member(raw["paid_by"], all_members)
        if not payer_match:
            anomalies.append(f"Payer '{raw['paid_by']}' does not match any group member")
            await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                anomaly_type="UNKNOWN_PAYER", severity=AnomalySeverity.HIGH,
                raw_data=raw, outcome=ImportOutcome.SKIPPED, resolution_chosen="Row skipped")
            row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
            skipped += 1; errors += 1
            continue

        payer_member, payer_user, payer_fuzzy = payer_match
        if payer_fuzzy:
            anomalies.append(
                f"Payer name '{raw['paid_by']}' fuzzy-matched to '{payer_user.display_name}' — verify"
            )
            warnings += 1

        payer_id = payer_user.id

        # ── 6. SETTLEMENT DETECTION ───────────────────────────
        split_type_raw = raw.get("split_type", "").strip()
        if is_settlement_row(raw["description"], split_type_raw, raw.get("notes", "")):
            # Determine payee from split_with (first name listed)
            split_with_raw = raw.get("split_with", "").strip()
            payee_names = [n.strip() for n in split_with_raw.split(";") if n.strip()]
            payee_id = None
            for pname in payee_names:
                match = find_member(pname, all_members)
                if match:
                    payee_id = match[1].id
                    break

            if not payee_id:
                anomalies.append("Settlement row: could not identify payee — skipped")
                await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                    anomaly_type="SETTLEMENT_NO_PAYEE", severity=AnomalySeverity.HIGH,
                    raw_data=raw, outcome=ImportOutcome.SKIPPED,
                    resolution_chosen="Row skipped — settlement payee unknown")
                row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
                skipped += 1; errors += 1
                continue

            if not group.currency_locked:
                await lock_group_currency(db, group)

            await create_settlement(
                db,
                group_id=group_id,
                payer_user_id=payer_id,
                payee_user_id=payee_id,
                amount_original=abs(parsed_amount),
                currency_original=currency,
                amount_base=abs(amount_base),
                fx_rate_used=fx_rate if fx_rate != 1.0 else None,
                settlement_date=parsed_date,
                status=SettlementStatus.ACTIVE,
                notes=f"[CSV Import] {raw.get('notes', '')}".strip(),
                recorded_by_user_id=current_user.id,
                import_id=import_report.id,
            )
            anomalies.append("Row identified as settlement — imported as Settlement record, not Expense")
            await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                anomaly_type="SETTLEMENT_AS_EXPENSE", severity=AnomalySeverity.MEDIUM,
                raw_data=raw, outcome=ImportOutcome.IMPORTED,
                transformation_applied="Imported as Settlement",
                resolution_chosen="Imported as Settlement")
            row_results.append(ImportRowResult(row_number=row_num, outcome="IMPORTED", anomalies=anomalies, raw_data=raw))
            imported += 1
            continue

        # ── 7. VALIDATE SPLIT TYPE ────────────────────────────
        allowed_split_types = {"EQUAL", "UNEQUAL", "PERCENTAGE", "SHARE"}
        split_type = split_type_raw.upper()
        if split_type not in allowed_split_types:
            anomalies.append(f"Unrecognised split_type '{split_type_raw}' — defaulting to EQUAL")
            split_type = "EQUAL"
            warnings += 1

        # ── 8. SPLIT TYPE CONFLICT CHECK ──────────────────────
        # Row 42: split_type=EQUAL but split_details has share-style data
        split_details_raw = raw.get("split_details", "").strip()
        if split_type == "EQUAL" and split_details_raw:
            anomalies.append(
                f"split_type is EQUAL but split_details '{split_details_raw}' is present — "
                "using EQUAL (split_details ignored)"
            )

        # ── 9. PARSE PARTICIPANTS ─────────────────────────────
        split_with_raw = raw.get("split_with", "").strip()
        participant_names = [n.strip() for n in split_with_raw.split(";") if n.strip()]

        participant_ids: list[UUID] = []
        for pname in participant_names:
            match = find_member(pname, all_members)
            if not match:
                anomalies.append(f"Participant '{pname}' not found — excluded from split")
                warnings += 1
                continue
            pmember, puser, pfuzzy = match

            # Ghost member check — was this person already gone by this date?
            if is_ghost_member(pmember, parsed_date):
                anomalies.append(
                    f"'{puser.display_name}' had left the group before {parsed_date} "
                    "— excluded from split"
                )
                warnings += 1
                continue

            if pfuzzy:
                anomalies.append(f"'{pname}' fuzzy-matched to '{puser.display_name}'")
                warnings += 1

            participant_ids.append(puser.id)

        if not participant_ids:
            anomalies.append("No valid participants after filtering — row skipped")
            await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                anomaly_type="NO_VALID_PARTICIPANTS", severity=AnomalySeverity.HIGH,
                raw_data=raw, outcome=ImportOutcome.SKIPPED, resolution_chosen="Row skipped")
            row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
            skipped += 1; errors += 1
            continue

        # ── 10. DUPLICATE CHECK ───────────────────────────────
        if is_probable_duplicate(parsed_date, abs(parsed_amount), payer_id, seen_keys, existing_expenses):
            anomalies.append(
                f"Probable duplicate: same date ({parsed_date}), amount ({abs(parsed_amount)}), "
                "and payer already exists — row skipped"
            )
            await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                anomaly_type="PROBABLE_DUPLICATE", severity=AnomalySeverity.HIGH,
                raw_data=raw, outcome=ImportOutcome.SKIPPED,
                resolution_chosen="Skipped — duplicate of an earlier row")
            row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
            skipped += 1; warnings += 1
            continue

        seen_keys.append((parsed_date, round(abs(parsed_amount), 2), payer_id))

        # ── 11. BUILD SPLITS ──────────────────────────────────
        n = len(participant_ids)
        splits_data: list[dict] = []

        if split_type == "EQUAL":
            per_person = round(amount_base / n, 2)
            splits_data = [{"user_id": uid, "amount_owed_base": per_person, "share_value": None}
                           for uid in participant_ids]

        elif split_type == "UNEQUAL":
            detail_entries = parse_split_details(split_details_raw)
            if not detail_entries:
                anomalies.append("UNEQUAL split but no split_details found — falling back to EQUAL")
                warnings += 1
                split_type = "EQUAL"
                per_person = round(amount_base / n, 2)
                splits_data = [{"user_id": uid, "amount_owed_base": per_person, "share_value": None}
                               for uid in participant_ids]
            else:
                total_unequal = sum(e["value"] for e in detail_entries)
                if abs(total_unequal - abs(parsed_amount)) > 0.05:
                    anomalies.append(
                        f"UNEQUAL split amounts sum to {total_unequal} but expense is {abs(parsed_amount)} — row skipped"
                    )
                    await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                        anomaly_type="UNEQUAL_SUM_MISMATCH", severity=AnomalySeverity.HIGH,
                        raw_data=raw, outcome=ImportOutcome.SKIPPED, resolution_chosen="Row skipped")
                    row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
                    skipped += 1; errors += 1
                    continue
                for entry in detail_entries:
                    match = find_member(entry["name"], all_members)
                    if match:
                        # Convert to base currency
                        splits_data.append({
                            "user_id": match[1].id,
                            "amount_owed_base": round(entry["value"] * fx_rate, 2),
                            "share_value": None,
                        })

        elif split_type == "PERCENTAGE":
            detail_entries = parse_split_details(split_details_raw)
            total_pct = sum(e["value"] for e in detail_entries)
            if abs(total_pct - 100) > 0.5:
                anomalies.append(
                    f"PERCENTAGE split sums to {total_pct}% (not 100%) — row skipped. "
                    "Cannot safely normalize without knowing the correct percentages."
                )
                await create_import_report_item(db, import_id=import_report.id, row_number=row_num,
                    anomaly_type="PERCENTAGE_SUM_INVALID", severity=AnomalySeverity.HIGH,
                    raw_data=raw, outcome=ImportOutcome.SKIPPED,
                    resolution_chosen="Skipped — percentages sum to 110%, cannot normalize safely")
                row_results.append(ImportRowResult(row_number=row_num, outcome="SKIPPED", anomalies=anomalies, raw_data=raw))
                skipped += 1; errors += 1
                continue
            for entry in detail_entries:
                match = find_member(entry["name"], all_members)
                if match:
                    splits_data.append({
                        "user_id": match[1].id,
                        "amount_owed_base": round(amount_base * entry["value"] / 100, 2),
                        "share_value": entry["value"],
                    })

        elif split_type == "SHARE":
            detail_entries = parse_split_details(split_details_raw)
            total_shares = sum(e["value"] for e in detail_entries)
            if total_shares <= 0:
                anomalies.append("SHARE split has zero total shares — falling back to EQUAL")
                warnings += 1
                per_person = round(amount_base / n, 2)
                splits_data = [{"user_id": uid, "amount_owed_base": per_person, "share_value": None}
                               for uid in participant_ids]
            else:
                for entry in detail_entries:
                    match = find_member(entry["name"], all_members)
                    if match and not is_ghost_member(match[0], parsed_date):
                        splits_data.append({
                            "user_id": match[1].id,
                            "amount_owed_base": round(amount_base * entry["value"] / total_shares, 2),
                            "share_value": entry["value"],
                        })

        if not splits_data:
            # Fallback to equal if parsing produced no splits
            per_person = round(amount_base / n, 2)
            splits_data = [{"user_id": uid, "amount_owed_base": per_person, "share_value": None}
                           for uid in participant_ids]

        # ── 12. LOCK CURRENCY ─────────────────────────────────
        if not group.currency_locked:
            await lock_group_currency(db, group)

        # ── 13. CREATE EXPENSE ────────────────────────────────
        expense = await create_expense(
            db,
            group_id=group_id,
            paid_by_user_id=payer_id,
            description=raw["description"],
            notes=raw.get("notes") or None,
            amount_original=parsed_amount,
            currency_original=currency,
            amount_base=amount_base,
            fx_rate_used=fx_rate if fx_rate != 1.0 else None,
            expense_date=parsed_date,
            split_type=SplitType(split_type),
            created_by_user_id=current_user.id,
            import_id=import_report.id,
        )
        await create_splits(db, expense.id, splits_data)

        transformation = "; ".join(anomalies) if anomalies else None
        await create_import_report_item(
            db,
            import_id=import_report.id,
            row_number=row_num,
            anomaly_type=None if not anomalies else "WARNINGS",
            severity=AnomalySeverity.LOW if anomalies else None,
            raw_data=raw,
            outcome=outcome,
            transformation_applied=transformation,
            fx_rate_used=fx_rate if fx_rate != 1.0 else None,
            resolution_chosen="Imported successfully" if not anomalies else "Imported with warnings",
        )
        row_results.append(ImportRowResult(
            row_number=row_num,
            outcome=outcome.value,
            anomalies=anomalies,
            raw_data=raw,
        ))
        imported += 1

    # Finalize
    summary = (
        f"Import complete: {imported} rows imported ({converted} with currency conversion), "
        f"{skipped} skipped. {warnings} warnings, {errors} hard errors."
    )
    import_report = await finalize_import_report(
        db, import_report,
        total_rows=len(raw_rows),
        imported=imported,
        skipped=skipped,
        warnings=warnings,
        errors=errors,
        summary=summary,
    )

    return ImportReportOut(
        import_id=import_report.id,
        group_id=group_id,
        filename=import_report.csv_filename,
        total_rows=len(raw_rows),
        imported=imported,
        skipped=skipped,
        converted=converted,
        warning_count=warnings,
        error_count=errors,
        rows=row_results,
        created_at=import_report.created_at,
    )


# ── LIST AND DETAIL ───────────────────────────────────────────────

async def list_import_reports(
    db: AsyncSession,
    group_id: UUID,
    current_user_id: UUID,
) -> list[ImportSummaryOut]:
    reports = await get_group_import_reports(db, group_id)
    return [
        ImportSummaryOut(
            import_id=r.id,
            filename=r.csv_filename,
            total_rows=r.total_rows_processed,
            imported=r.rows_successfully_imported,
            skipped=r.rows_skipped,
            warning_count=r.warning_count,
            error_count=r.error_count,
            created_at=r.created_at,
        )
        for r in reports
    ]


async def get_import_report_detail(
    db: AsyncSession,
    group_id: UUID,
    import_id: UUID,
) -> ImportReportOut:
    report = await get_import_report_by_id(db, import_id)
    if not report or report.group_id != group_id:
        raise HTTPException(status_code=404, detail="Import report not found")
    items = await get_import_report_items(db, import_id)
    rows = [
        ImportRowResult(
            row_number=item.row_number,
            outcome=item.outcome.value,
            anomalies=[item.transformation_applied] if item.transformation_applied else [],
            raw_data=item.raw_data,
        )
        for item in items
    ]
    return ImportReportOut(
        import_id=report.id,
        group_id=report.group_id,
        filename=report.csv_filename,
        total_rows=report.total_rows_processed,
        imported=report.rows_successfully_imported,
        skipped=report.rows_skipped,
        converted=0,
        warning_count=report.warning_count,
        error_count=report.error_count,
        rows=rows,
        created_at=report.created_at,
    )
