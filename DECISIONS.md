# DECISIONS.md — Engineering Decision Log

Each entry follows: Decision → Options Considered → Choice Made → Why.

---

## 1. Balance Storage: Dynamic vs Stored

**Decision:** Should balances be stored in a `balances` table or computed on demand?

**Options:**
- A. Stored balance column per member, updated on every expense/settlement write
- B. Computed dynamically from `expense_splits` and `settlements` on every read

**Choice:** B — Dynamic computation.

**Why:** Storing balances introduces the risk of the stored value going out of sync with the underlying data (especially when expenses are soft-deleted or settlements are voided). For a flatmate group with ~50–200 expenses, computing the balance is fast and always accurate. If scale becomes a concern later, a materialized view or cache can be added without changing the data model.

---

## 2. Settlement Deletion: Hard vs Soft

**Decision:** Can settlements be deleted?

**Options:**
- A. Hard delete
- B. Soft delete (is_deleted flag)
- C. Status-based: ACTIVE / VOIDED — no delete at all

**Choice:** C — Status-based (VOIDED), no deletion.

**Why:** Settlements represent financial facts. Deleting a settlement obscures that it ever happened, which is bad for auditing and trust between flatmates. VOIDED keeps the record visible but removes it from balance calculations. This matches how accounting systems handle reversals.

---

## 3. Expense Deletion: Hard vs Soft Delete

**Decision:** Should deleting an expense remove the row from the database?

**Options:**
- A. Hard delete (DELETE FROM expenses WHERE id = ...)
- B. Soft delete (is_deleted = true)

**Choice:** B — Soft delete.

**Why:** Expenses may be referenced by `import_reports`. Deleting them would break the import audit trail. A soft delete keeps history intact and allows undo if needed.

---

## 4. Currency Handling

**Decision:** How do we handle expenses in a currency different from the group's base?

**Options:**
- A. Reject non-base-currency expenses
- B. Store original amount only, convert at display time
- C. Store both original amount AND converted base amount (with the rate used)

**Choice:** C — Store both.

**Why:** Option B means the balance calculation result can change over time as exchange rates move, making it impossible to audit past calculations. Storing the rate at the time of the expense ensures reproducible, auditable balances. This also directly addresses Priya's complaint ("the sheet pretends a dollar is a rupee").

**API:** Frankfurter (free, no key required). If unavailable at import time, the row is skipped and flagged.

---

## 5. Group Currency Lock

**Decision:** Can the group's base currency change after creation?

**Options:**
- A. Allow currency change at any time
- B. Lock currency after the first expense is added

**Choice:** B — Lock after first expense.

**Why:** If the currency could change, all existing base-currency amounts would become wrong (they were converted at different rates). Locking ensures the group always has a consistent unit of account.

---

## 6. Split Types Supported

**Decision:** Which split types to implement?

**Options considered:** Equal, Exact/Unequal, Percentage, Shares, Custom formula

**Choice:** Four types — EQUAL, UNEQUAL, PERCENTAGE, SHARE — exactly the four that appear in the CSV.

**Why:** These cover every real-world case in the dataset. EQUAL is the default. UNEQUAL covers the birthday cake (someone explicitly not charged). PERCENTAGE covers the pizza and brunch rows. SHARE covers the scooter rentals (bigger scooters = more shares).

---

## 7. Duplicate Detection Strategy

**Decision:** How do we detect duplicate CSV rows?

**Options:**
- A. Exact string match on description
- B. Same date + same payer + same amount (within ±₹0.01)
- C. Semantic similarity (NLP)

**Choice:** B — same date, payer, and amount.

**Why:** Description strings vary ("Dinner at Marina Bites" vs "dinner - marina bites"). Amount and date are the financial facts. Option C is over-engineering for a flat of 5 people. Option B catches the Marina Bites duplicate (rows 5–6) correctly without false positives.

**Exception:** The Thalassa dinner (rows 24–25) has different payers AND different amounts, so the duplicate check does not fire. Both are imported with a warning. The user must manually delete the wrong one.

---

## 8. Negative Amount Policy (Refunds)

**Decision:** Is a negative amount in the CSV an error or a valid refund?

**Options:**
- A. Reject all negative amounts as data errors
- B. Accept and import as a refund (negative expense)

**Choice:** B — import as refund.

**Why:** Row 26 ("Parasailing refund, -$30") is clearly a partial refund from a cancelled slot. Rejecting it would leave Dev's balance incorrect. A negative expense naturally inverts the balance effect (Dev gets credit back, participants get their share back).

---

## 9. Ghost Member Policy (Meera in April)

**Decision:** What happens when a CSV row lists a participant who had already left the group?

**Options:**
- A. Reject the entire row
- B. Import the expense but exclude the ghost member from the split
- C. Re-add the ghost member temporarily

**Choice:** B — exclude ghost member, import the rest.

**Why:** The expense itself is real (groceries were bought). Only the split list is wrong. Excluding Meera and splitting among the remaining active members is the most financially accurate interpretation. We warn explicitly so the user can review.

---

## 10. Settlement-as-Expense Detection

**Decision:** Rows 14 and 38 are payments, not shared expenses. How do we handle them?

**Options:**
- A. Skip them (they're not valid expenses)
- B. Import them as expenses anyway (wrong type, but they're in the CSV)
- C. Auto-detect and import as Settlement records

**Choice:** C — auto-detect and import as correct type.

**Why:** Silently skipping means the debt is never recorded. Importing as an expense distorts balances. The correct type is Settlement. We detect these using a combination of signals: empty `split_type`, "paid…back" in description, "deposit + moving in" in notes.

---

## 11. Authentication: JWT Strategy

**Decision:** Access token vs session vs OAuth?

**Choice:** Stateless JWT with short-lived access tokens (15 min) + long-lived refresh tokens (7 days) stored in HttpOnly cookies.

**Why:** No server-side session storage needed (good for stateless deployment on Railway). HttpOnly cookies for refresh tokens prevent XSS token theft. Short access token expiry limits the damage of a leaked token.

---

## 12. Password Hashing: passlib vs bcrypt directly

**Decision:** Use passlib's `CryptContext` or call bcrypt directly?

**Initially:** Used passlib's `CryptContext(schemes=["bcrypt"])`.

**Problem discovered:** passlib 1.7.4 internally calls `bcrypt.hashpw()` with a 73-byte test string to detect a "wrap bug". bcrypt 4+ raises `ValueError` for passwords over 72 bytes, breaking passlib's internal self-test even for normal-length passwords.

**Final choice:** Remove passlib. Call bcrypt directly: `bcrypt.hashpw()`, `bcrypt.checkpw()`, `bcrypt.gensalt()`.

**Why:** Passlib is effectively unmaintained. Direct bcrypt calls are simpler, explicit, and have no hidden compatibility issues.

---

## 13. Percentage Sum > 100%: Skip or Normalize?

**Decision:** Row 15 has percentages that sum to 110%. Should we normalize (divide by 1.1) or skip?

**Choice:** Skip with HIGH error.

**Why:** Normalizing would silently change each person's financial obligation without their knowledge. For example, if the intent was "Meera pays 10%", normalizing would give her 18.18%. We cannot make that decision on behalf of the users. The correct action is to surface the error and let the user fix and re-import.
