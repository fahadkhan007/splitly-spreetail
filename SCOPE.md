# SCOPE.md — Anomaly Log & Database Schema

## Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `users` | Registered accounts. Stores hashed password, email, verified status. |
| `groups` | A flat/household group. Has a base currency that locks after the first expense. |
| `group_members` | Membership history. `joined_at` and `left_at` track exactly when each person was in the group. |
| `invitations` | Email invitations sent by admins. Status: PENDING → ACCEPTED or CANCELLED. |
| `expenses` | Every shared expense. Stores both original currency amount and base-currency amount (for FX). `is_deleted` enables soft-delete. |
| `expense_splits` | One row per person per expense. `amount_owed_base` is the figure used in all balance calculations. |
| `settlements` | Payments between members to reduce debt. Can only be VOIDED, never deleted. |
| `import_reports` | Summary of each CSV import session (row counts, error counts). |
| `import_report_items` | One row per CSV row processed. Records every anomaly, transformation, and outcome. |

### Key Design Decisions
- Balances are **never stored** — always calculated dynamically from expenses, splits, and settlements.
- `expense_splits.amount_owed_base` is always in the **group's base currency**, regardless of the expense's original currency. This ensures consistent arithmetic.
- `group_members.left_at` makes balance calculations **date-aware**: we can tell exactly who was a member at the time of any expense.

---

## Anomaly Log — expenses_export.csv

All 17 anomalies found in the file and the policy applied to each.

---

### Anomaly 1 — Duplicate row (rows 5 & 6)
**Problem:** Two rows for "Marina Bites dinner" on 08-02-2026 paid by Dev for ₹3200. Row 6 has no notes; row 5 has "Dev visiting for the weekend".  
**Detection:** Same date + same payer + same amount already seen in this session.  
**Policy:** Import row 5 (first occurrence). Skip row 6 as PROBABLE_DUPLICATE.  
**Severity:** HIGH (row skipped)

---

### Anomaly 2 — Comma-formatted amount (row 7)
**Problem:** Electricity amount is `"1,200"` (Excel-style thousands separator, quoted in CSV).  
**Detection:** `parse_amount()` strips all commas before parsing.  
**Policy:** Auto-fix: strip comma → parse as 1200. Log as LOW transformation.  
**Severity:** LOW (auto-fixed, imported)

---

### Anomaly 3 — Lowercase payer name (row 9)
**Problem:** `paid_by = "priya"` instead of `"Priya"`.  
**Detection:** Case-insensitive name matching.  
**Policy:** Match to "Priya" silently. LOW log entry.  
**Severity:** LOW (auto-fixed, imported)

---

### Anomaly 4 — Fuzzy payer name "Priya S" (row 11)
**Problem:** `paid_by = "Priya S"` — extra initial, not an exact match.  
**Detection:** No exact match found. First-word fuzzy match finds "Priya".  
**Policy:** Fuzzy-match to "Priya". Import with MEDIUM warning (human should verify).  
**Severity:** MEDIUM (imported with warning)

---

### Anomaly 5 — Missing payer (row 13)
**Problem:** `paid_by` is empty. Notes say "can't remember who paid".  
**Detection:** Required field check.  
**Policy:** Cannot import an expense with no payer. Skip with HIGH error.  
**Severity:** HIGH (row skipped)

---

### Anomaly 6 — Settlement logged as expense (row 14)
**Problem:** "Rohan paid Aisha back ₹5000". `split_type` is blank. Notes: "this is a settlement not an expense??"  
**Detection:** Empty `split_type` AND "paid…back" in description.  
**Policy:** Import as a **Settlement** record (Rohan → Aisha, ₹5000), not as an Expense. Logged as SETTLEMENT_AS_EXPENSE anomaly.  
**Severity:** MEDIUM (handled, imported as correct type)

---

### Anomaly 7 — Percentages sum to 110% (row 15)
**Problem:** Pizza Friday split: Aisha 30% + Rohan 30% + Priya 30% + Meera 20% = 110%. Notes: "percentages might be off".  
**Detection:** Sum of parsed percentages ≠ 100 (tolerance ±0.5).  
**Policy:** Skip. We cannot safely normalize — reducing any one person's share is a financial decision only the users can make.  
**Severity:** HIGH (row skipped)

---

### Anomaly 8 — Foreign currency amounts (rows 20, 21, 23, 26)
**Problem:** Goa trip expenses in USD ($540 villa, $84 lunch, $150 parasailing, -$30 refund).  
**Detection:** `currency` field is "USD", group base is "INR".  
**Policy:** Fetch live exchange rate from Frankfurter API. Convert to INR. Store both original amount and base amount. Log rate used. Import as CONVERTED.  
**Severity:** INFO (auto-handled, imported)

---

### Anomaly 9 — Unknown participant "Dev's friend Kabir" (row 23)
**Problem:** Parasailing split includes "Dev's friend Kabir" who is not a registered group member.  
**Detection:** No exact or fuzzy name match found.  
**Policy:** Exclude Kabir from the split. Import the expense among the 4 known members (Aisha, Rohan, Priya, Dev). Warn.  
**Severity:** MEDIUM (imported, Kabir excluded)

---

### Anomaly 10 — Probable duplicate Thalassa dinner (rows 24 & 25)
**Problem:** Row 24: Aisha logged "Dinner at Thalassa" ₹2400. Row 25: Rohan logged "Thalassa dinner" ₹2450. Notes on row 25: "Aisha also logged this I think hers is wrong."  
**Detection:** Different payers and different amounts — not caught by exact duplicate check. Both imported (the notes are ambiguous; we cannot make a financial judgment).  
**Policy:** Import both with a MEDIUM warning noting they may be duplicates of the same event. User must manually delete one.  
**Severity:** MEDIUM (both imported with warning)

---

### Anomaly 11 — Negative amount / refund (row 26)
**Problem:** "Parasailing refund" amount is `-30` USD. One slot was cancelled.  
**Detection:** `parsed_amount < 0`.  
**Policy:** Import as a negative expense (refund). Each participant's `amount_owed_base` becomes negative, which naturally reduces Dev's credit in balance calculations. This is the correct financial effect.  
**Severity:** INFO (imported as refund)

---

### Anomaly 12 — Non-standard date format "Mar-14" (row 27)
**Problem:** Date is "Mar-14" — month abbreviation + day, no year.  
**Detection:** All standard date formats fail. A special `%b-%d` pattern is tried.  
**Policy:** Parse as March 14, 2026 (year assumed from surrounding data). Log MEDIUM warning.  
Also: `paid_by = "rohan "` has trailing whitespace — auto-trimmed.  
**Severity:** MEDIUM (imported with warning)

---

### Anomaly 13 — Missing currency (row 28)
**Problem:** Groceries DMart — currency field is empty. Notes: "forgot to set currency".  
**Detection:** Currency field is blank or not 3 letters.  
**Policy:** Default to group base currency (INR). Log MEDIUM warning.  
**Severity:** MEDIUM (imported with warning)

---

### Anomaly 14 — Zero amount (row 31)
**Problem:** "Dinner order Swiggy" amount is 0. Notes: "counted twice earlier - fixing later".  
**Detection:** `parsed_amount == 0`.  
**Policy:** Skip. A zero-amount expense has no financial effect and the notes confirm it's a placeholder.  
**Severity:** HIGH (row skipped)

---

### Anomaly 15 — Ambiguous date "04-05-2026" (row 34)
**Problem:** Deep cleaning service. Date could be April 5 OR May 4. Notes confirm ambiguity.  
**Detection:** When using DD-MM-YYYY format (primary for this CSV), both day and month are ≤ 12, so an alternate reading is valid.  
**Policy:** Interpret as April 5, 2026 (DD-MM-YYYY, consistent with rest of file). Log MEDIUM warning flagging the ambiguity.  
**Severity:** MEDIUM (imported with warning)

---

### Anomaly 16 — Ghost member: Meera in April (row 36)
**Problem:** "Groceries BigBasket" dated April 2, 2026 includes Meera in `split_with`. Meera left end of March.  
**Detection:** `is_ghost_member()` checks if participant's `left_at` date is before the expense date.  
**Policy:** Exclude Meera from the split. Import expense among Aisha, Rohan, Priya only. Warn.  
**Severity:** MEDIUM (imported, Meera excluded)

---

### Anomaly 17 — "Sam deposit share" is a settlement (row 38)
**Problem:** Sam pays Aisha ₹15,000 for his room deposit. Notes: "Sam moving in! paid Aisha his deposit". `split_type = equal` but this is clearly a one-directional payment.  
**Detection:** "deposit" in description AND "moving in" in notes.  
**Policy:** Import as a **Settlement** (Sam → Aisha, ₹15,000), not as an expense.  
**Severity:** MEDIUM (handled, imported as correct type)

---

### Anomaly 18 — split_type conflict (row 42)
**Problem:** `split_type = equal` but `split_details = "Aisha 1; Rohan 1; Priya 1; Sam 1"` (share-style data). Notes: "split_type says equal but someone added shares anyway".  
**Detection:** `split_type == EQUAL` but `split_details` is non-empty.  
**Policy:** Trust the declared `split_type`. Since 1:1:1:1 shares IS equal, the result is the same either way. Log LOW warning, import as EQUAL.  
**Severity:** LOW (auto-handled, imported)
