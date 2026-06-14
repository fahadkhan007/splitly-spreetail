# AI_CONTEXT.md — Splitly (Shared Expenses Application)
> **Single Source of Truth** — Updated continuously throughout the project lifecycle.
> **Rule:** Never delete historical information. Superseded decisions are marked `[SUPERSEDED]`.
> **Purpose:** Any engineer or AI agent must be able to reconstruct the entire project from this file alone.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Assignment Summary & Deliverables](#2-assignment-summary--deliverables)
3. [Confirmed Decisions (Pre-Discovery)](#3-confirmed-decisions-pre-discovery)
4. [Open Questions & Discovery Log](#4-open-questions--discovery-log)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Business Rules](#7-business-rules)
8. [CSV Import — Anomaly Catalogue](#8-csv-import--anomaly-catalogue)
9. [Database Design](#9-database-design)
10. [API Design](#10-api-design)
11. [Backend Architecture](#11-backend-architecture)
12. [Frontend Architecture](#12-frontend-architecture)
13. [Authentication & Authorization Strategy](#13-authentication--authorization-strategy)
14. [CSV Import Workflow](#14-csv-import-workflow)
15. [Anomaly Handling Policies](#15-anomaly-handling-policies)
16. [Reporting](#16-reporting)
17. [Deployment Strategy](#17-deployment-strategy)
18. [Testing Strategy](#18-testing-strategy)
19. [Documentation Plan](#19-documentation-plan)
20. [Project Status & Task Tracking](#20-project-status--task-tracking)
21. [Decision History](#21-decision-history)

---

## 1. Project Overview

**Application Name:** Splitly ✅ CONFIRMED
**Type:** Shared Expenses / Bill Splitting Platform
**Inspiration:** Splitwise
**Context:** SDE Internship Assignment (job assignment)
**Target Users:** Students and flatmates (personal/household use, not enterprise)

**Tech Stack:**
| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+) |
| Frontend | React 18 + Vite + **TypeScript** ✅ CONFIRMED |
| Database | PostgreSQL |
| ORM | **SQLAlchemy** (declarative base, separate models/ and schemas/) |
| Auth | JWT (stateless) — email + password |
| Email Service | Resend (via Resend API) |
| Python Package Manager | uv |
| JS Package Manager | npm |
| Deployment | Railway (backend + DB) + Vercel (frontend) |

**Repository Structure:** Monorepo (`splitly-spreetail/` root)
```
splitly-spreetail/
├── .gitignore
├── .git/
├── AI_CONTEXT.md
├── docker-compose.yml
├── backend/          ← FastAPI + uv
└── frontend/         ← React + npm
```

**Code Style Mandate:**
- Simple, readable code — every function does one thing
- No advanced FastAPI patterns: use plain `= Depends(fn)` not `Annotated[X, Depends(fn)]`
- No complex SQLAlchemy magic — plain FK columns and straightforward queries
- Comments explain *why*, not just *what*
- If a junior dev can't read it in 30 seconds, rewrite it

---

## 2. Assignment Summary & Deliverables

The application must:
- Support user authentication
- Support groups with changing memberships over time
- Track expenses with multiple split types (equal, unequal, percentage, ratio/share)
- Track settlements as a separate entity from expenses
- Calculate balances (group-level and member-to-member)
- Import the provided CSV (`Expenses Export.csv`) without manual pre-editing
- Detect, surface, and handle anomalies in the CSV with user confirmation
- Generate import reports
- Never silently modify data
- Support reporting and analytics
- Be deployable

**Primary Deliverable:** Working application + all design artifacts + defensible interview answers.

---

## 3. Confirmed Decisions (Pre-Discovery)

These decisions were captured from `AI_USAGE.md` and are considered locked unless explicitly revisited.

### 3.1 Group Membership Model
- **Decision:** Time-bound membership with `join_date` and `left_date` per member.
- **Rationale:** Allows accurate historical balance calculation (member only owes for expenses during their membership window).
- **Impact:** Queries for "who was in the group on date X" become: `WHERE join_date <= X AND (left_date IS NULL OR left_date >= X)`.

### 3.2 Multi-Currency Strategy
- **Decision:** User specifies a **base currency** for the group/import. All amounts are converted to base currency before calculation.
- **Conversion:** Use a third-party live FX API for conversion rates at time of transaction.
- **Simplicity Rule:** Keep the implementation as simple as possible while being correct.
- **Final Display:** After calculations, optionally display in any currency using live rates.

### 3.3 Ratio / Share Split Type
- **Decision:** `total_amount / sum(all_ratios) × individual_ratio = individual_share`
- **Example:** Amount = 3600, ratios = [1, 2, 1, 2] → sum = 6 → shares = [600, 1200, 600, 1200]

### 3.4 Settlements
- **Decision:** Settlements are a **separate table/entity**, NOT a special expense type.
- **Decision:** Balance is recalculated after each settlement and stored/updated.
- **Rejected:** Using `type=settlement` flag on the expenses table. [REASON: violates separation of concerns; makes balance queries complex]

### 3.5 Supported Split Types
- `equal` — divide amount equally among all members
- `unequal` — explicit amount per member (must sum to total)
- `percentage` — explicit percentage per member (must sum to 100%)
- `share` / `ratio` — ratio-based split (see 3.3)

### 3.6 Balance Types
- **Type 1 — Group Balance:** Total amount each person owes/is owed across the entire group (net)
- **Type 2 — Member-to-Member Balance:** How much Person A owes Person B specifically

### 3.7 CSV Import Philosophy
- Import CSV directly without manual pre-editing.
- On anomaly detection: surface to user, request confirmation.
- On hard errors (e.g., missing paid_by, missing amount): ask user which row to include/exclude.
- On duplicates: present both rows and ask user which to keep.
- **Never silently modify data.**

---

## 4. Open Questions & Discovery Log

### Round 1 — Core Product & Scope ✅ COMPLETE
- [x] Q1: App name = **Splitly**. Target = **students and flatmates** (personal/household). Not enterprise.
- [x] Q2: **Stateless JWT auth** with email + password. No OAuth in scope.
- [x] Q3: Users join groups via **email invitation** (Splitwise-style). Email delivered via **Resend API**.
- [x] Q4: **Multi-group supported**. Users see a group list. Expenses before join / after leave are excluded from the invitee's balance calculation.
- [x] Q5: Group closes when: (a) all members leave, OR (b) creator explicitly deletes. Group history (expenses + settlements) is **always preserved** (soft delete / archival).

### Round 2 — Auth, User Flows & Roles ✅ COMPLETE
- [x] Q6: Registration fields = name + email + password. `is_verified` flag on users table. Login allowed immediately but inviting/adding expenses requires verified email. Uniqueness enforced on **email only** (not name).
- [x] Q7: Any member can add expenses and record settlements. Only the **admin (creator)** can delete the group. [OPEN MICRO: who can send invitations? — to resolve Round 3]
- [x] Q8: If creator leaves without deleting → **auto-promote next longest-standing member** (ordered by `joined_at`) to admin.
- [x] Q9: Invite contains a signed token. Invite link → new user lands on register page → auto-joins group after registration. Existing user → auto-joins on link click (authenticated). Invite can be **resent unlimited times** (new token each resend). No expiry defined (open: should we add one for security?).
- [x] Q10: **Access token (short-lived) + Refresh token (long-lived)**. Logout and token blacklisting NOT implemented in v1. Refresh token stored in HttpOnly cookie. No server-side token revocation table for now.

### Round 3 — Expenses, Settlements & Balance Mechanics ✅ COMPLETE
- [x] Q11: **Edit/delete permissions:** Any active member can CREATE. Only **payer (paid_by) OR admin** can edit/delete. If payer has left, admin retains that right.
- [x] Q12: **Balances are NEVER stored in DB.** Always calculated dynamically from expenses + settlements on request. No materialized balance table.
- [x] Q13: **Settlements cannot be permanently deleted.** Can be marked `VOIDED` by the recorder or admin. Voided record stays in DB for audit. Voided settlements are excluded from balance calculations.
- [x] Q14: **User selects or creates a group BEFORE importing CSV.** All imported expenses land in that group. Non-existent users in CSV → imported as `PENDING` members and surfaced as anomalies.
- [x] Q15: **Base currency set at group creation, locked after first expense.** Expenses stored in both original currency AND base-currency-converted amount. Balance calculations use base currency. FX rate applied at time of expense date.

### Round 4 — CSV Import & Anomaly Handling ✅ COMPLETE
- [x] Q16: **FX API = Frankfurter.app** (free, no key, historical ECB rates). If unavailable at import: ASK USER (B: enter rate manually OR C: use most recent available rate + flag in report).
- [x] Q17: **Pending member model fully defined** — see Section 5.10 and Section 15 for complete spec.
- [x] Q18: **All HIGH-severity anomaly policies = ASK USER.** General rule: never silently modify financial data. See Section 15 for per-anomaly policy table.
- [x] Q19: **Import report = Option C (DB-stored + downloadable)**. Tables: `ImportReport` + `ImportReportItem`. Formats: JSON + CSV. Full field list in Section 16.2.
- [x] Q20: **Invite tokens expire after 7 days.** Resend creates new token, invalidates previous. Unlimited resends allowed.

### Round 5 — Reporting, Architecture & Deployment ✅ COMPLETE
- [x] Q21: **Reports in scope:** (1) Group expense summary, (2) Member balance sheet, (3) Settlement history, (4) Monthly spending breakdown. No expense categories in v1.
- [x] Q22: **ORM = SQLModel.** Models and schemas are SEPARATE: `models/` for SQLModel DB classes, `schemas/` for pure Pydantic API request/response classes. Layer architecture: `Router → Service → Repository → DB`.
- [x] Q23: **Frontend:** React + React Router v6 + Zustand (auth/global state) + TanStack React Query (server state) + CSS Modules. UI inspired by Splitwise (left nav, center feed, right balance panel). Minimal but polished.
- [x] Q24: **Deployment:** Backend (FastAPI) + PostgreSQL → Railway. Frontend (React) → Vercel. `docker-compose.yml` for local development.
- [x] Q25: **Testing:** Backend unit tests (balance calculation, split math, anomaly detection) + integration tests (API endpoints via pytest + httpx). Frontend: no tests in v1. Tests written at end of implementation.

---

## 5. Functional Requirements

### 5.1 Authentication
- Email + password login
- Stateless JWT-based authentication
- Email invitations delivered via Resend API
- Password reset — NOT in v1 scope (deferred)
- JWT strategy: short-lived **access token** + long-lived **refresh token** (HttpOnly cookie)
- Logout / token blacklisting: NOT implemented in v1
- `is_verified` boolean flag on `users` table
- Login is allowed immediately after registration (before email verification)
- Verified email required to: send group invitations, add expenses

### 5.2 User Management
- Registration fields: display name + email + password
- Email uniqueness enforced at DB level (unique constraint on `users.email`)
- Display name uniqueness NOT enforced platform-wide (only email is unique identifier)
- `is_verified` boolean, default false; set to true after email verification click
- User can belong to multiple groups simultaneously
- Dashboard shows list of all groups the user is a member of

### 5.3 Groups
- Create a group (creator becomes admin, role stored in `group_members.role`)
- Invite members by email (verified email required for inviter)
- Time-bound membership: `joined_at` and `left_at` timestamps per member in `group_members`
- Expenses before `joined_at` and after `left_at` are excluded from that member's balance
- Group lifecycle: `ACTIVE` → `CLOSED` (soft delete, data preserved)
- Group closes when: (a) all members leave, OR (b) admin explicitly deletes it
- Admin transfer: if current admin leaves, member with earliest `joined_at` is auto-promoted
- Multiple groups per user — fully supported
- [OPEN MICRO: who can send invitations — admin only or any member?]

### 5.4 Expenses
- Any active group member (verified email) can CREATE an expense
- **Edit/Delete authorization:**
  - Allowed: the expense payer (`paid_by`) OR a group admin
  - If payer has left the group: admin retains edit/delete rights
  - All other members: read-only on others' expenses
- Supported split types: `equal`, `unequal`, `percentage`, `share` (ratio)
- Expenses carry: description, amount (original), currency (original), amount_base (converted), expense_date, group_id, paid_by_user_id, split_type, notes
- Balance impact: only members with `joined_at ≤ expense_date AND (left_at IS NULL OR left_at ≥ expense_date)` are eligible split participants
- Editing an expense: re-validates split math; balances recalculated on next request (no stored state to update)

### 5.5 Settlements
- Any active group member (verified email) can RECORD a settlement
- Settlements are a separate table from expenses
- Settlement fields: recorder_user_id, payer_user_id, payee_user_id, amount, currency, amount_base, settlement_date, group_id, status, notes
- Settlement status enum: `ACTIVE` | `VOIDED`
- **VOIDED by:** the original recorder or a group admin
- **Cannot be permanently deleted** — voided record persists for audit
- Voided settlements are excluded from all balance calculations
- Settlement history is always preserved and visible in the group ledger

### 5.6 Balances
- **NEVER stored in database** — always computed dynamically on request
- Algorithm: SUM(expense splits owed) - SUM(settlements paid/received, excluding VOIDED) = net balance
- Type 1 — **Group net balance:** For each member, net amount they owe or are owed across the entire group
- Type 2 — **Member-to-member balance:** Exact amount Person A owes Person B (directional)
- Time-bound: calculations respect `joined_at` / `left_at` per member per expense date
- Currency: all balance values reported in group base currency

### 5.7 CSV Import
- User MUST select or create a group BEFORE initiating an import
- All imported expenses and any detected settlements belong to that selected group
- Import pipeline: `UPLOAD → PARSE → VALIDATE → DETECT ANOMALIES → SURFACE TO USER → USER RESOLVES → CONFIRM → COMMIT`
- Non-existent members found in CSV → created as `PENDING` group members (anomaly surfaced, user must confirm)
- User confirms or reassigns each HIGH-severity anomaly before final commit
- **Never silently modify financial data** — every transformation logged in import report
- Import report generated, stored in DB, and made downloadable after each session
- FX conversion: Frankfurter.app historical rates at expense date
- FX fallback: if API unavailable → ASK USER (manual rate entry OR use most recent cached rate + flag)

### 5.8 Anomaly Detection
- 21 anomaly types catalogued in Section 8 (see full table)
- Each anomaly surfaced with: row number, raw CSV data, anomaly type, severity, suggested resolution, required user action
- HIGH-severity: always ASK USER — no automatic resolution
- MEDIUM-severity: auto-resolve with logged transformation where unambiguous; ASK USER where financially significant
- LOW-severity: auto-resolve (case normalization, precision rounding) with transformation logged
- INFO-severity: log only, no user action required
- Resolution policies fully defined in Section 15

### 5.9 Currency
- Each group has exactly ONE `base_currency` field, set at creation
- Base currency is **locked** after the group's first expense is added
- All expenses stored with: `amount_original`, `currency_original`, `amount_base`, `fx_rate_used`
- FX rate applied at the date of the expense (historical rates via Frankfurter.app)
- Balance calculations use `amount_base` exclusively
- Assignment CSV: group base currency = INR; USD rows converted to INR at historical rate

### 5.10 Pending Members
- A **pending member** is a person found in imported CSV data who has no registered Splitly account
- Pending members are stored in the system (likely as a `users` record with `status = PENDING`, no password)
- Pending members CAN: appear in groups, participate in expenses and settlements, have balances calculated
- Pending members CANNOT: log in, create, edit, or view any data
- Admins CAN: send an invite email to convert a pending member to a registered user
- On registration via invite: pending member record linked to new account; all historical data preserved
- If never registers: balances and history remain permanently in the group
- Admin can REMOVE a pending member ONLY if they are not referenced by any expense or settlement
- If referenced: pending member can be marked `INACTIVE` but historical records remain intact

---

## 6. Non-Functional Requirements

*(To be populated during discovery)*

---

## 7. Business Rules

*(To be populated during discovery)*

---

## 8. CSV Import — Anomaly Catalogue

> Source: `Expenses Export.csv` (43 data rows, 44 total lines including header)
> All anomalies identified by AI pre-discovery analysis.

### 8.1 Identified Anomalies

| # | Row | Description | Anomaly Type | Severity |
|---|-----|-------------|-------------|---------|
| 1 | 5,6 | "Dinner at Marina Bites" and "dinner - marina bites" — same amount (3200), same date (08-02-2026), same payer (Dev). Likely duplicate. | Probable Duplicate | HIGH |
| 2 | 7 | Amount `"1,200"` — comma inside quotes (locale-formatted number, not a valid decimal) | Amount Format Error | MEDIUM |
| 3 | 9 | `paid_by = "priya"` (lowercase) — name case inconsistency vs "Priya" elsewhere | Name Case Inconsistency | LOW |
| 4 | 10 | Amount `899.995` — more than 2 decimal places (sub-paisa precision) | Precision Anomaly | LOW |
| 5 | 11 | `paid_by = "Priya S"` — ambiguous name (is this the same "Priya"?) | Ambiguous Member Identity | HIGH |
| 6 | 12 | `unequal` split: Rohan 700 + Priya 400 + Meera 400 = 1500 ✓ — Aisha excluded (her birthday) | Valid Exclusion (edge case) | INFO |
| 7 | 13 | `paid_by` is empty — no payer recorded | Missing Required Field | HIGH |
| 8 | 14 | "Rohan paid Aisha back" — described as a settlement in notes, but formatted as an expense row | Settlement Masquerading as Expense | HIGH |
| 9 | 15 | Pizza Friday percentages: 30+30+30+20 = 110% — does not sum to 100% | Percentage Sum Error | HIGH |
| 10 | 20 | Amount in USD (540) — foreign currency in an INR-dominant dataset | Currency Mismatch | MEDIUM |
| 11 | 21 | Amount in USD (84) — foreign currency | Currency Mismatch | MEDIUM |
| 12 | 23 | `split_with` includes "Dev's friend Kabir" — non-member participant | Non-Member in Split | HIGH |
| 13 | 24,25 | "Dinner at Thalassa" (Aisha, 2400) and "Thalassa dinner" (Rohan, 2450) — possible duplicate, different amounts/payers | Possible Duplicate (conflicting) | HIGH |
| 14 | 26 | Amount = -30 USD — negative amount (refund) | Negative Amount / Refund | MEDIUM |
| 15 | 27 | Date = "Mar-14" — non-standard date format | Date Format Error | MEDIUM |
| 16 | 28 | `currency` field is empty | Missing Currency | MEDIUM |
| 17 | 31 | Amount = 0 — zero amount expense | Zero Amount | MEDIUM |
| 18 | 34 | Date "04-05-2026" — ambiguous: April 5 or May 4? Note says "format is a mess" | Ambiguous Date | MEDIUM |
| 19 | 36 | `split_with` includes "Meera" but notes say "Meera still in the group list" after she moved out (row 33 notes she's leaving) | Stale Member in Split | MEDIUM |
| 20 | 38 | "Sam deposit share" — described as deposit payment to Aisha; semantically ambiguous (settlement? onboarding fee?) | Ambiguous Transaction Type | MEDIUM |
| 21 | 42 | `split_type = "equal"` but `split_details` contains share ratios `1;1;1;1` — contradictory fields | Contradictory Split Type vs Details | MEDIUM |

**Total Anomalies Identified: 21**

### 8.2 Anomaly Handling Policies

**Global Rule:** For all HIGH-severity anomalies, the system MUST NOT silently modify financial data. User review is required before the import pipeline continues.

| # | Anomaly | Severity | Policy | Options Presented to User |
|---|---------|----------|--------|---------------------------|
| 1 | Probable duplicate (rows 5,6) | HIGH | ASK USER | Keep row 5 / Keep row 6 / Keep both |
| 2 | Amount `"1,200"` locale format | MEDIUM | AUTO-RESOLVE | Strip commas → 1200.00 (logged in report) |
| 3 | `paid_by = "priya"` (lowercase) | LOW | AUTO-RESOLVE | Case-normalize to matched member name (logged) |
| 4 | Amount `899.995` (3 decimal places) | LOW | AUTO-RESOLVE | Round to 2 decimal places → 900.00 (logged) |
| 5 | `paid_by = "Priya S"` (ambiguous) | HIGH | ASK USER | Map to existing member / Create as new member |
| 6 | Aisha excluded from birthday cake | INFO | LOG ONLY | No action required (valid unequal split) |
| 7 | Missing `paid_by` (row 13) | HIGH | ASK USER | Assign a payer / Skip this row |
| 8 | Settlement logged as expense (row 14) | HIGH | ASK USER | Import as expense / Convert to settlement / Skip row |
| 9 | Percentage sum ≠ 100% (row 15, sums to 110%) | HIGH | ASK USER | Normalize to 100% / Skip row |
| 10 | USD amount (row 20) | MEDIUM | AUTO-RESOLVE | Convert to INR using Frankfurter historical rate (logged) |
| 11 | USD amount (row 21) | MEDIUM | AUTO-RESOLVE | Convert to INR using Frankfurter historical rate (logged) |
| 12 | Non-member in split ("Kabir", row 23) | HIGH | ASK USER | Add as pending member / Remove from split / Skip row |
| 13 | Conflicting possible duplicate (rows 24,25) | HIGH | ASK USER | Keep row 24 / Keep row 25 / Keep both / Skip both |
| 14 | Negative amount — refund (-30 USD, row 26) | MEDIUM | ASK USER | Import as refund (negative expense) / Skip row |
| 15 | Non-standard date `"Mar-14"` (row 27) | MEDIUM | AUTO-RESOLVE | Parse to 2026-03-14 (logged) |
| 16 | Missing currency (row 28) | MEDIUM | ASK USER | Use group base currency (INR) / Skip row |
| 17 | Zero amount (row 31) | MEDIUM | ASK USER | Import as ₹0 expense / Skip row |
| 18 | Ambiguous date `"04-05-2026"` (row 34) | MEDIUM | ASK USER | Interpret as April 5 / Interpret as May 4 |
| 19 | Stale member Meera in split (row 36) | MEDIUM | ASK USER | Remove Meera from split / Import as-is |
| 20 | Ambiguous transaction type — deposit (row 38) | MEDIUM | ASK USER | Import as expense / Convert to settlement / Skip row |
| 21 | Contradictory split_type vs details (row 42) | MEDIUM | ASK USER | Trust split_type (equal, ignore details) / Trust details (treat as share split) |

---

## 9. Database Design

> **ORM:** SQLAlchemy (declarative base pattern — `Base = declarative_base()`)
> **DB:** PostgreSQL
> **Convention:** All PKs are UUIDs. All tables have `created_at` and `updated_at` timestamps.
> **Soft deletes:** Used for groups; settlements use status enum instead.
> **Schemas:** Separate Pydantic `BaseModel` classes in `schemas/` folder (not mixed with DB models)

### 9.1 Entity Relationship Summary

```
users
  ├── group_members ───► groups
  ├── invitations ────► groups
  ├── expenses (paid_by_user_id) ───► groups
  ├── expense_splits (user_id) ──► expenses
  ├── settlements (payer + payee) ─► groups
  ├── import_reports ────────► groups
  └── import_report_items ────► import_reports
```

### 9.2 Table Definitions

#### Table: `users`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default gen_random_uuid() | |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Login identifier |
| `display_name` | VARCHAR(100) | NOT NULL | Not unique |
| `password_hash` | VARCHAR(255) | NULLABLE | NULL for PENDING users |
| `is_verified` | BOOLEAN | NOT NULL, DEFAULT false | Email verification status |
| `status` | ENUM('ACTIVE','PENDING','INACTIVE') | NOT NULL, DEFAULT 'ACTIVE' | PENDING = imported from CSV, no account |
| `avatar_url` | VARCHAR(500) | NULLABLE | Optional profile image |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Auto-updated |

**Indexes:** `users_email_idx` UNIQUE on `email`
**Business rules:**
- PENDING users have no `password_hash`; they cannot log in
- When a PENDING user registers via invite, record is updated: status → ACTIVE, password_hash set, is_verified set

---

#### Table: `groups`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `name` | VARCHAR(100) | NOT NULL | Display name |
| `description` | TEXT | NULLABLE | Optional group description |
| `base_currency` | VARCHAR(3) | NOT NULL | ISO 4217 code e.g. 'INR', 'USD' |
| `currency_locked` | BOOLEAN | NOT NULL, DEFAULT false | True after first expense added |
| `status` | ENUM('ACTIVE','CLOSED') | NOT NULL, DEFAULT 'ACTIVE' | |
| `created_by_user_id` | UUID | FK → users.id, NOT NULL | Original creator (may change if admin leaves) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `groups_status_idx` on `status`
**Business rules:**
- `currency_locked` set to true when first expense is inserted
- CLOSED groups retain all data; no new expenses/settlements can be added

---

#### Table: `group_members`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `group_id` | UUID | FK → groups.id, NOT NULL | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `role` | ENUM('ADMIN','MEMBER') | NOT NULL, DEFAULT 'MEMBER' | |
| `joined_at` | TIMESTAMPTZ | NOT NULL | Set when invite accepted |
| `left_at` | TIMESTAMPTZ | NULLABLE | NULL = currently active member |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `group_members_group_user_idx` UNIQUE on `(group_id, user_id)` (one membership record per user per group)
- `group_members_active_idx` on `(group_id, left_at)` for fast active-member lookups

**Business rules:**
- Active member query: `WHERE group_id = ? AND (left_at IS NULL)`
- Member-on-date query: `WHERE group_id = ? AND joined_at <= ? AND (left_at IS NULL OR left_at >= ?)`
- When admin leaves: find member with smallest `joined_at` where `left_at IS NULL`, set role → ADMIN

---

#### Table: `invitations`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `group_id` | UUID | FK → groups.id, NOT NULL | |
| `invited_by_user_id` | UUID | FK → users.id, NOT NULL | Must be admin |
| `invited_email` | VARCHAR(255) | NOT NULL | Email the invite was sent to |
| `token` | VARCHAR(512) | NOT NULL, UNIQUE | Signed JWT or UUID token |
| `status` | ENUM('PENDING','ACCEPTED','EXPIRED','CANCELLED') | NOT NULL, DEFAULT 'PENDING' | |
| `expires_at` | TIMESTAMPTZ | NOT NULL | now() + 7 days |
| `accepted_by_user_id` | UUID | FK → users.id, NULLABLE | Set when accepted |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `invitations_token_idx` UNIQUE on `token`; `invitations_email_group_idx` on `(invited_email, group_id)`
**Business rules:**
- On resend: previous `PENDING` invite for same email+group set to `CANCELLED`; new record created
- On accept: `status → ACCEPTED`, `accepted_by_user_id` set, `group_members` record created
- Expired check: `expires_at < now()` → reject with 410 Gone

---

#### Table: `expenses`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `group_id` | UUID | FK → groups.id, NOT NULL | |
| `paid_by_user_id` | UUID | FK → users.id, NOT NULL | Who paid |
| `description` | VARCHAR(500) | NOT NULL | |
| `amount_original` | NUMERIC(12,2) | NOT NULL | Raw amount as entered |
| `currency_original` | VARCHAR(3) | NOT NULL | ISO 4217 |
| `amount_base` | NUMERIC(12,2) | NOT NULL | Converted to group base currency |
| `fx_rate_used` | NUMERIC(18,6) | NULLABLE | 1.0 if same currency |
| `expense_date` | DATE | NOT NULL | Date of the expense (not created_at) |
| `split_type` | ENUM('EQUAL','UNEQUAL','PERCENTAGE','SHARE') | NOT NULL | |
| `notes` | TEXT | NULLABLE | Free-text notes |
| `import_id` | UUID | FK → import_reports.id, NULLABLE | Set if created via CSV import |
| `created_by_user_id` | UUID | FK → users.id, NOT NULL | Who entered this expense |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `expenses_group_date_idx` on `(group_id, expense_date)` for chronological feeds
- `expenses_paid_by_idx` on `paid_by_user_id`
- `expenses_import_idx` on `import_id`

---

#### Table: `expense_splits`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `expense_id` | UUID | FK → expenses.id, NOT NULL | |
| `user_id` | UUID | FK → users.id, NOT NULL | Who owes this share |
| `amount_owed_base` | NUMERIC(12,2) | NOT NULL | In group base currency |
| `share_value` | NUMERIC(10,4) | NULLABLE | Raw ratio/percentage/amount as entered |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `expense_splits_expense_idx` on `expense_id`; `expense_splits_user_idx` on `user_id`
**Business rules:**
- For EQUAL split: `amount_owed_base = expense.amount_base / count(splits)`
- For PERCENTAGE: `amount_owed_base = expense.amount_base * (percentage / 100)`; `share_value` = percentage
- For SHARE: `amount_owed_base = expense.amount_base * (ratio / sum_all_ratios)`; `share_value` = ratio
- For UNEQUAL: `amount_owed_base` = direct amount; must sum to `expense.amount_base`
- Validation: SUM(amount_owed_base) must equal expense.amount_base (±0.01 rounding tolerance)

---

#### Table: `settlements`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `group_id` | UUID | FK → groups.id, NOT NULL | |
| `payer_user_id` | UUID | FK → users.id, NOT NULL | Who paid |
| `payee_user_id` | UUID | FK → users.id, NOT NULL | Who received |
| `amount_original` | NUMERIC(12,2) | NOT NULL | |
| `currency_original` | VARCHAR(3) | NOT NULL | |
| `amount_base` | NUMERIC(12,2) | NOT NULL | Converted to group base currency |
| `fx_rate_used` | NUMERIC(18,6) | NULLABLE | |
| `settlement_date` | DATE | NOT NULL | |
| `status` | ENUM('ACTIVE','VOIDED') | NOT NULL, DEFAULT 'ACTIVE' | |
| `notes` | TEXT | NULLABLE | |
| `recorded_by_user_id` | UUID | FK → users.id, NOT NULL | Who created this record |
| `voided_by_user_id` | UUID | FK → users.id, NULLABLE | Who voided it |
| `voided_at` | TIMESTAMPTZ | NULLABLE | |
| `import_id` | UUID | FK → import_reports.id, NULLABLE | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `settlements_group_idx` on `(group_id, status)`; `settlements_payer_idx` on `payer_user_id`
**Business rules:**
- `payer_user_id != payee_user_id` (CHECK constraint)
- VOIDED settlements are excluded from all balance calculations
- Cannot be hard-deleted

---

#### Table: `import_reports`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `group_id` | UUID | FK → groups.id, NOT NULL | |
| `initiated_by_user_id` | UUID | FK → users.id, NOT NULL | |
| `csv_filename` | VARCHAR(255) | NOT NULL | |
| `total_rows_processed` | INTEGER | NOT NULL | |
| `rows_successfully_imported` | INTEGER | NOT NULL | |
| `rows_skipped` | INTEGER | NOT NULL | |
| `warning_count` | INTEGER | NOT NULL, DEFAULT 0 | |
| `error_count` | INTEGER | NOT NULL, DEFAULT 0 | |
| `final_summary` | TEXT | NULLABLE | Human-readable summary |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Import timestamp |

---

#### Table: `import_report_items`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `import_id` | UUID | FK → import_reports.id, NOT NULL | |
| `row_number` | INTEGER | NOT NULL | CSV row index |
| `anomaly_type` | VARCHAR(100) | NULLABLE | e.g. 'PROBABLE_DUPLICATE' |
| `severity` | ENUM('HIGH','MEDIUM','LOW','INFO') | NULLABLE | |
| `raw_data` | JSONB | NOT NULL | Original CSV row snapshot |
| `resolution_chosen` | VARCHAR(200) | NULLABLE | User's choice |
| `transformation_applied` | TEXT | NULLABLE | Description of auto-transform |
| `fx_rate_used` | NUMERIC(18,6) | NULLABLE | |
| `outcome` | ENUM('IMPORTED','SKIPPED','CONVERTED') | NOT NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `import_report_items_import_idx` on `import_id`

---

### 9.3 Relationships Summary

| Relationship | Type | Notes |
|-------------|------|-------|
| users ↔ groups | M:M via group_members | One user can be in many groups |
| groups → expenses | 1:M | Each expense belongs to one group |
| expenses → expense_splits | 1:M | One expense has N split rows |
| users → expenses (paid_by) | M:1 | Many expenses paid by one user |
| users → expense_splits | M:1 | Many splits owed by one user |
| groups → settlements | 1:M | Settlements scoped to group |
| groups → invitations | 1:M | Pending invites per group |
| import_reports → import_report_items | 1:M | Line items per import session |

### 9.4 Balance Calculation Algorithm

```
For each member M in group G:

  amount_paid = SUM(expenses.amount_base WHERE paid_by_user_id = M)

  amount_owed = SUM(expense_splits.amount_owed_base WHERE user_id = M
                    AND expense is in group G
                    AND expense.expense_date >= M.joined_at
                    AND (M.left_at IS NULL OR expense.expense_date <= M.left_at))

  settlements_paid_out = SUM(settlements.amount_base
                             WHERE payer_user_id = M AND status = 'ACTIVE')

  settlements_received  = SUM(settlements.amount_base
                             WHERE payee_user_id = M AND status = 'ACTIVE')

  net_balance = amount_paid - amount_owed + settlements_paid_out - settlements_received

  Positive net_balance → others owe M
  Negative net_balance → M owes others
```

---

## 10. API Design

*(To be populated after discovery is complete)*

---

## 11. Backend Architecture

### 11.1 Framework & Language
- FastAPI (Python 3.11+)
- **SQLAlchemy** (ORM — declarative base, plain class-based models)
- **Pydantic v2** (separate schema classes for API request/response)
- Alembic (database migrations)
- Uvicorn (ASGI server)

### 11.2 Request Flow
```
HTTP Request
  ↓
FastAPI Router     (HTTP only: parse input, call service, return response)
  ↓
Service Layer      (business logic, orchestrates repositories)
  ↓
Repository Layer   (DB queries only via SQLAlchemy Session)
  ↓
PostgreSQL
```

### 11.3 Folder Structure
```
backend/
├── app/
│   ├── main.py               # FastAPI app, router registration, CORS
│   ├── config.py             # Settings (pydantic-settings, reads .env)
│   ├── database.py           # SQLAlchemy engine, Session factory, get_db dependency
│   ├── models/               # SQLAlchemy ORM classes (inherit from Base)
│   │   ├── user.py
│   │   ├── group.py
│   │   ├── group_member.py
│   │   ├── invitation.py
│   │   ├── expense.py
│   │   ├── expense_split.py
│   │   ├── settlement.py
│   │   ├── import_report.py
│   │   └── import_report_item.py
│   ├── schemas/              # Pure Pydantic request/response schemas
│   │   ├── auth.py             # LoginRequest, TokenResponse, RegisterRequest
│   │   ├── user.py             # UserOut, UserUpdate
│   │   ├── group.py            # GroupCreate, GroupOut, GroupUpdate
│   │   ├── member.py           # MemberOut, MemberUpdate
│   │   ├── expense.py          # ExpenseCreate, ExpenseOut, ExpenseUpdate
│   │   ├── settlement.py       # SettlementCreate, SettlementOut
│   │   ├── balance.py          # BalanceOut, MemberBalanceOut
│   │   ├── csv_import.py       # ImportInitiate, AnomalyOut, ResolutionIn, ImportReportOut
│   │   └── reports.py          # SummaryOut, MonthlyOut
│   ├── routers/              # FastAPI APIRouter instances
│   │   ├── auth.py             # /auth/register, /auth/login, /auth/refresh, /auth/verify
│   │   ├── users.py            # /users/me
│   │   ├── groups.py           # /groups CRUD
│   │   ├── members.py          # /groups/{id}/members
│   │   ├── invitations.py      # /groups/{id}/invitations, /invitations/accept
│   │   ├── expenses.py         # /groups/{id}/expenses CRUD
│   │   ├── settlements.py      # /groups/{id}/settlements CRUD
│   │   ├── balances.py         # /groups/{id}/balances
│   │   ├── csv_import.py       # /groups/{id}/import (multi-step)
│   │   └── reports.py          # /groups/{id}/reports/*
│   ├── services/             # Business logic (no direct DB access)
│   │   ├── auth_service.py     # register, login, verify_email, refresh_token
│   │   ├── group_service.py    # create_group, close_group, transfer_admin
│   │   ├── member_service.py   # join, leave, remove_member
│   │   ├── expense_service.py  # create_expense, validate_split, edit, delete
│   │   ├── settlement_service.py # create_settlement, void_settlement
│   │   ├── balance_service.py  # calculate_group_balance, calculate_member_balance
│   │   ├── csv_import_service.py # orchestrates full import pipeline
│   │   ├── anomaly_service.py  # detect all 21 anomaly types
│   │   ├── fx_service.py       # Frankfurter API wrapper, fallback handling
│   │   └── report_service.py   # summary, monthly, settlement history
│   ├── repositories/         # DB queries only (no business logic)
│   │   ├── user_repo.py
│   │   ├── group_repo.py
│   │   ├── member_repo.py
│   │   ├── invitation_repo.py
│   │   ├── expense_repo.py
│   │   ├── settlement_repo.py
│   │   └── import_repo.py
│   ├── core/
│   │   ├── security.py         # JWT create/decode, password hash/verify
│   │   ├── email.py            # Resend API wrapper
│   │   ├── dependencies.py     # get_current_user, require_group_member, require_admin
│   │   └── exceptions.py       # Custom HTTP exceptions
│   └── tests/
│       ├── conftest.py         # DB fixtures, test client, auth helpers
│       ├── unit/
│       │   ├── test_balance_service.py
│       │   ├── test_split_math.py
│       │   └── test_anomaly_detection.py
│       └── integration/
│           ├── test_auth.py
│           ├── test_groups.py
│           ├── test_expenses.py
│           ├── test_settlements.py
│           └── test_csv_import.py
├── alembic/                  # Database migrations
├── Dockerfile
├── requirements.txt
├── .env.example
└── pyproject.toml
```

### 11.4 Key Dependencies
```
fastapi
uvicorn[standard]
sqlalchemy              # ORM
alembic                 # DB migrations
psycopg2-binary         # PostgreSQL driver
pydantic[email]         # Schema validation (comes with fastapi)
pydantic-settings       # .env config
python-jose[cryptography] # JWT
bcrypt                  # Password hashing
resend                  # Email API
httpx                   # FX API calls + async test client
python-multipart        # File upload (CSV)
pytest
pytest-asyncio
```

---

## 12. Frontend Architecture

### 12.1 Stack
- React 18 + Vite
- React Router v6
- Zustand (auth state, current group context)
- TanStack React Query (server state, caching, loading/error)
- CSS Modules (scoped, component-level styles)
- Axios (HTTP client, configured with JWT interceptors)

### 12.2 UI Design Direction
- Inspired by Splitwise: left nav sidebar, center expense feed, right balance panel
- Minimal, clean, functional — not heavy/complex
- Mobile-responsive (flexbox/grid)

### 12.3 Folder Structure
```
frontend/
├── src/
│   ├── main.jsx              # React root, router setup
│   ├── App.jsx               # Route definitions
│   ├── api/                  # Axios instance + API call functions
│   │   ├── client.js           # Axios instance (baseURL, interceptors, token attach)
│   │   ├── auth.js
│   │   ├── groups.js
│   │   ├── expenses.js
│   │   ├── settlements.js
│   │   ├── balances.js
│   │   ├── csvImport.js
│   │   └── reports.js
│   ├── stores/               # Zustand stores
│   │   ├── authStore.js        # currentUser, accessToken, isAuthenticated
│   │   └── groupStore.js       # currentGroupId, currentGroup
│   ├── hooks/                # React Query custom hooks
│   │   ├── useGroups.js
│   │   ├── useExpenses.js
│   │   ├── useBalances.js
│   │   ├── useSettlements.js
│   │   └── useImport.js
│   ├── components/           # Reusable UI components
│   │   ├── layout/
│   │   │   ├── Sidebar.jsx         # Left nav: groups list, nav links
│   │   │   ├── BalancePanel.jsx    # Right panel: group balances
│   │   │   └── TopBar.jsx
│   │   ├── expenses/
│   │   │   ├── ExpenseFeed.jsx
│   │   │   ├── ExpenseCard.jsx
│   │   │   └── AddExpenseModal.jsx
│   │   ├── settlements/
│   │   │   └── SettleUpModal.jsx
│   │   ├── import/
│   │   │   ├── ImportWizard.jsx    # Multi-step: upload → review → resolve → confirm
│   │   │   ├── AnomalyCard.jsx     # One anomaly with resolution options
│   │   │   └── ImportReport.jsx    # Post-import summary
│   │   └── common/
│   │       ├── Button.jsx
│   │       ├── Modal.jsx
│   │       ├── Badge.jsx           # VOIDED, PENDING, ACTIVE tags
│   │       └── CurrencyAmount.jsx  # Formats amounts with currency symbol
│   ├── pages/                # Route-level page components
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── VerifyEmailPage.jsx
│   │   ├── DashboardPage.jsx   # Groups list, recent activity
│   │   ├── GroupPage.jsx       # Main group view (feed + balances)
│   │   ├── GroupSettingsPage.jsx
│   │   ├── ImportPage.jsx      # CSV import wizard
│   │   ├── ReportsPage.jsx     # Group reports
│   │   └── InviteAcceptPage.jsx # Invite link landing page
│   └── styles/
│       ├── global.css          # CSS variables, resets
│       └── [component].module.css
├── index.html
├── vite.config.js
├── package.json
└── .env.example
```

### 12.4 Route Map
| Path | Component | Auth Required |
|------|-----------|---------------|
| `/login` | LoginPage | No |
| `/register` | RegisterPage | No |
| `/verify-email` | VerifyEmailPage | No |
| `/invite/accept/:token` | InviteAcceptPage | Optional |
| `/dashboard` | DashboardPage | Yes |
| `/groups/:id` | GroupPage | Yes (member) |
| `/groups/:id/settings` | GroupSettingsPage | Yes (admin) |
| `/groups/:id/import` | ImportPage | Yes (admin) |
| `/groups/:id/reports` | ReportsPage | Yes (member) |

---

## 13. Authentication & Authorization Strategy

### 13.1 Authentication Mechanism
- **Type:** Stateless JWT (JSON Web Tokens)
- **Credentials:** Email + password (no OAuth in scope)
- **Password Storage:** bcrypt hashed (industry standard, slow-by-design for brute-force resistance)
- **Access Token:** Short-lived (e.g., 15 minutes) — exact duration TBD
- **Refresh Token:** Long-lived (e.g., 7 days), stored in HttpOnly cookie
- **No token blacklist:** Logout NOT implemented in v1. Access token valid until expiry.
- **Email Service:** Resend API for: verification emails, invitation emails

### 13.2 Authorization Model — Permissions Matrix
| Action | Any Active Member | Payer Only | Admin Only |
|--------|------------------|-----------|------------|
| View group & expenses | ✅ | — | — |
| Add expense | ✅ (verified) | — | — |
| Edit own expense | — | ✅ | — |
| Delete own expense | — | ✅ | — |
| Edit/delete any expense | — | — | ✅ |
| Record settlement | ✅ (verified) | — | — |
| Void own settlement | ✅ (recorder) | — | — |
| Void any settlement | — | — | ✅ |
| Send invitation | — | — | ✅ |
| Remove member | — | — | ✅ |
| Delete group | — | — | ✅ |
| Import CSV | — | — | ✅ |
| View/download import report | ✅ | — | — |

> **Note:** "Payer" in the table above means the `paid_by` user on that specific expense. If the payer has left the group, the admin inherits those rights.

### 13.3 Invitation Flow
- Admin sends invite by email → Resend delivers email with signed token link
- Token contains: `group_id`, `invited_email`, `expires_at` (7 days from send)
- **New user flow:** Click link → Register page (email pre-filled) → Verify email → Auto-join group
- **Existing user flow:** Click link (while authenticated) → Auto-join group immediately
- **Expired invite:** Cannot be accepted. Admin must resend (generates new token, old token invalidated)
- **Pending member invite:** Admin sends invite to pending member's email → same flow; on registration the pending record is linked to new account
- Unlimited resends allowed
- Invite decline: not tracked (user simply does not click the link)

---

## 14. CSV Import Workflow

### 14.1 Pre-Import
1. User authenticates (admin role required to import)
2. User selects an existing group OR creates a new group
3. User uploads the CSV file
4. System validates file is valid CSV with expected headers

### 14.2 Parse & Validate
5. System parses all rows into structured objects
6. Each row validated for: required fields, data types, date formats, amount formats, currency codes, split math
7. Each validation issue classified by anomaly type and severity

### 14.3 Anomaly Detection
8. All 21 anomaly types checked (see Section 8)
9. Duplicate detection: fuzzy match on (date, amount, payer, description)
10. Name disambiguation: case-insensitive match against existing group members
11. Currency detection: rows with foreign currency flagged against group base currency

### 14.4 User Review (Anomaly Resolution UI)
12. System presents all anomalies grouped by severity
13. HIGH-severity anomalies: user MUST resolve before proceeding
14. MEDIUM-severity: user reviews auto-proposed resolution or overrides
15. LOW/INFO: shown in summary; user can proceed without action
16. User actions per anomaly: accept suggestion / override / skip row

### 14.5 Commit
17. After all HIGH anomalies resolved: user clicks "Confirm Import"
18. System processes rows in order:
    - Creates pending members where needed
    - Fetches FX rates from Frankfurter.app (with fallback to user input if unavailable)
    - Calculates `amount_base` for each expense
    - Inserts expenses, splits, and any settlements into DB
    - Logs every transformation and resolution
19. Import report created and stored in `ImportReport` + `ImportReportItem` tables

### 14.6 Post-Import
20. User sees import summary screen
21. User can download report as JSON or CSV
22. Balances recalculated dynamically on next view (no action needed)

---

## 15. Anomaly Handling Policies

See **Section 8.2** for the complete per-anomaly policy table with all 21 entries.

**Global Principles:**
1. **No silent financial modification** — every change to amount, currency, or split must be user-approved or logged
2. **HIGH-severity = always ASK USER** — import is blocked until resolved
3. **MEDIUM-severity = propose auto-resolution, user can override**
4. **LOW-severity = auto-resolve silently, log transformation in import report**
5. **INFO = log only, no user action**
6. **FX unavailability** — present user with: (B) enter rate manually, OR (C) use most recent cached rate and flag in report
7. **Pending members** — created automatically for unrecognized names confirmed by user; admin must later invite them to register

---

## 16. Reporting

### 16.1 Application Reports ✅ DEFINED

| Report | Description | Endpoint |
|--------|-------------|----------|
| Group expense summary | Total spent, per-member contribution, filterable by date range | `GET /groups/{id}/reports/summary` |
| Member balance sheet | Net balance per member (both balance types) | `GET /groups/{id}/balances` |
| Settlement history | All settlements with ACTIVE/VOIDED status | `GET /groups/{id}/settlements` |
| Monthly spending breakdown | Expenses grouped and summed by month | `GET /groups/{id}/reports/monthly` |

All report data computed dynamically (no pre-aggregated tables needed for this scale).

### 16.2 Import Report ✅ DEFINED
**Storage:** `ImportReport` table (one per import session) + `ImportReportItem` table (one per anomaly/transformation)

**ImportReport fields:**
- `import_id` (UUID, PK)
- `group_id` (FK)
- `initiated_by_user_id` (FK)
- `import_timestamp`
- `csv_filename`
- `total_rows_processed`
- `rows_successfully_imported`
- `rows_skipped`
- `warning_count`
- `error_count`
- `final_summary` (text)

**ImportReportItem fields:**
- `item_id` (UUID, PK)
- `import_id` (FK)
- `row_number`
- `anomaly_type`
- `severity`
- `raw_data` (JSON snapshot of original CSV row)
- `resolution_chosen`
- `transformation_applied`
- `fx_rate_used` (nullable)
- `outcome` (IMPORTED / SKIPPED / CONVERTED)

**Download formats:** JSON, CSV
**Access:** Any group member can view/download the import report for their group

---

## 17. Deployment Strategy

### 17.1 Environments
| Environment | Backend | Frontend | Database |
|-------------|---------|----------|----------|
| Local Dev | FastAPI (uvicorn) | React (vite dev) | PostgreSQL (docker-compose) |
| Production | Railway | Vercel | Railway PostgreSQL |

### 17.2 Local Development
- `docker-compose.yml` at project root
- Services: `postgres`, `backend` (FastAPI), optionally `pgadmin`
- Frontend runs separately with `npm run dev` (Vite)
- `.env` file for local secrets (never committed)
- `.env.example` committed with all required variable names

### 17.3 Production Deployment
**Backend → Railway:**
- `Dockerfile` in `backend/`
- Railway auto-detects and builds
- PostgreSQL provisioned as Railway plugin
- Environment variables set in Railway dashboard
- Auto-deploy on push to `main` branch

**Frontend → Vercel:**
- Connect GitHub repo to Vercel
- Build command: `npm run build`
- `VITE_API_URL` environment variable points to Railway backend URL
- Auto-deploy on push to `main` branch

### 17.4 Environment Variables
**Backend (.env):**
```
DATABASE_URL=postgresql://...
SECRET_KEY=<jwt-signing-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
RESEND_API_KEY=<resend-key>
FRONTEND_URL=https://splitly.vercel.app
FRANKFURTER_BASE_URL=https://api.frankfurter.app
```
**Frontend (.env):**
```
VITE_API_URL=https://splitly-backend.railway.app
```

---

## 18. Testing Strategy

### 18.1 Backend Tests (pytest)
**Unit Tests — Service Layer:**
- Balance calculation: all member combinations, time-bound exclusion, voided settlements
- Split math: equal, unequal, percentage (edge: sum ≠ 100%), share/ratio
- Anomaly detection: each of the 21 anomaly types with fixture CSV rows
- FX conversion: with mock Frankfurter responses

**Integration Tests — API Layer (pytest + httpx):**
- Auth: register, verify email, login, token refresh
- Groups: create, invite, join, leave, admin transfer
- Expenses: CRUD + permission enforcement (non-payer cannot edit)
- Settlements: create, void, balance impact
- CSV import: full pipeline with anomaly resolution
- Balances: correctness after expense + settlement combinations

### 18.2 Frontend Tests
- Not in v1 scope

### 18.3 Test Tooling
- `pytest` + `pytest-asyncio` for async FastAPI tests
- `httpx` async test client
- `pytest-cov` for coverage reporting
- Separate test database (test schema or SQLite in-memory for unit tests)

---

## 19. Documentation Plan

### 19.1 In-Code Documentation
- Docstrings on all service and repository functions
- Type annotations throughout (FastAPI enforces this via Pydantic)

### 19.2 API Documentation
- Auto-generated via FastAPI's built-in Swagger UI (`/docs`) and ReDoc (`/redoc`)
- All routes, request bodies, and response schemas documented via Pydantic models

### 19.3 Project Documentation
- `README.md` — project overview, local setup instructions, environment variables
- `AI_CONTEXT.md` — this file; complete living technical specification
- `AI_USAGE.md` — AI tool usage log (already exists)
- Import report (auto-generated per import session, downloadable)

---

## 20. Project Status & Task Tracking

### Phase
`DISCOVERY — COMPLETE — Database Design Finalization`

### Completed
- [x] Read and analyzed CSV file — identified 21 anomalies
- [x] Captured pre-existing decisions from AI_USAGE.md
- [x] Created AI_CONTEXT.md v0.1
- [x] Round 1: Core product & scope — all 5 questions answered
- [x] Round 2: Auth, user flows & roles — all 5 questions answered
- [x] Round 3: Expenses, settlements & balance mechanics — all 5 questions answered
- [x] Round 4: CSV import & anomaly handling — all 5 questions answered
- [x] Round 5: Reporting, architecture & deployment — all 5 questions answered
- [x] Discovery complete — all major product and technical decisions locked

### In Progress
- [ ] Database schema finalization (presenting to user for review)
- [ ] API design
- [ ] Implementation planning

### Pending
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Testing
- [ ] Deployment

---

## 21. Decision History

| Date | Decision | Rationale | Source |
|------|----------|-----------|--------|
| 2026-06-13 | Time-bound membership model | Accurate historical balances | AI_USAGE.md |
| 2026-06-13 | Multi-currency with user-specified base currency + FX API | Simplicity + correctness | AI_USAGE.md |
| 2026-06-13 | Ratio split = total ÷ sum(ratios) × individual_ratio | Simple, standard, defensible | AI_USAGE.md |
| 2026-06-13 | Settlements = separate table, not an expense flag | Separation of concerns | AI_USAGE.md |
| 2026-06-13 | Balance Types: Group net + Member-to-member | User-stated requirement | AI_USAGE.md |
| 2026-06-13 | CSV: surface anomalies, require user confirmation | Never silently modify data | AI_USAGE.md |
| 2026-06-13 | App name = Splitly (confirmed) | Product identity | Round 1 Discovery |
| 2026-06-13 | Target users = students and flatmates | Scope definition | Round 1 Discovery |
| 2026-06-13 | Auth = stateless JWT, email + password | Standard, defensible, full ownership | Round 1 Discovery |
| 2026-06-13 | Email invitations via Resend API | Splitwise-style UX, simple integration | Round 1 Discovery |
| 2026-06-13 | Pre-join and post-leave expenses excluded from member balances | Fairness; users only owe for their active period | Round 1 Discovery |
| 2026-06-13 | Multi-group support: user can be in N groups simultaneously | Product requirement | Round 1 Discovery |
| 2026-06-13 | Group closes on: all members leave OR creator explicit delete | Lifecycle clarity | Round 1 Discovery |
| 2026-06-13 | Group history always preserved after closure (soft delete) | Data integrity, audit | Round 1 Discovery |
| 2026-06-13 | Expense edit/delete: payer OR admin only; admin inherits if payer left | Accountability + admin override | Round 3 Discovery |
| 2026-06-13 | Balances never stored in DB — always derived dynamically | Simplicity, correctness, avoids stale state bugs | Round 3 Discovery |
| 2026-06-13 | Settlements: VOIDED status (not deleted), audit trail preserved | Audit integrity, dispute prevention | Round 3 Discovery |
| 2026-06-13 | Voided settlements excluded from balance calculations | Correctness | Round 3 Discovery |
| 2026-06-13 | CSV import: user selects group first; all rows land in that group | UX clarity, data ownership | Round 3 Discovery |
| 2026-06-13 | Non-existent CSV members → PENDING members, surfaced as anomalies | No silent data creation | Round 3 Discovery |
| 2026-06-13 | Base currency set at group creation, locked after first expense | Historical accuracy, no retroactive recalculation | Round 3 Discovery |
| 2026-06-13 | Expenses stored with both original currency and base-currency amount + FX rate | Audit trail, enables re-conversion if needed | Round 3 Discovery |
| 2026-06-14 | FX API = Frankfurter.app (free, historical, no key) | No cost, no setup, interview-simple | Round 4 Discovery |
| 2026-06-14 | FX fallback: ASK USER (manual rate or most recent cached) | No silent financial assumptions | Round 4 Discovery |
| 2026-06-14 | ALL HIGH-severity anomalies = ASK USER policy | Financial integrity, never guess | Round 4 Discovery |
| 2026-06-14 | LOW anomalies auto-resolved (case norm, precision rounding), logged | User experience + audit trail | Round 4 Discovery |
| 2026-06-14 | Import report: DB-stored (ImportReport + ImportReportItem) + downloadable JSON/CSV | Audit + assignment requirement | Round 4 Discovery |
| 2026-06-14 | Invite tokens expire after 7 days; resend creates new token, invalidates old | Security + UX simplicity | Round 4 Discovery |
| 2026-06-14 | Pending members: DB record (no login), full expense participation, admin can invite to register | Data completeness + real-world CSV handling | Round 4 Discovery |
| 2026-06-14 | Admin can remove pending member only if unreferenced; else mark INACTIVE | Data integrity | Round 4 Discovery |
| 2026-06-14 | Invitations: admin-only permission to send | Access control, group safety | Round 4 Discovery |
| 2026-06-14 | Permissions matrix fully defined (see Section 13.2) | Authorization clarity | Round 4 Discovery |
| 2026-06-14 | Reports in scope: expense summary, balance sheet, settlement history, monthly breakdown | Useful for flatmates, computable from existing data | Round 5 Discovery |
| 2026-06-14 | [SUPERSEDED] ORM = SQLModel | Replaced by SQLAlchemy decision below | Round 5 Discovery |
| 2026-06-14 | **ORM = SQLAlchemy** (declarative base, models/ separate from schemas/) | Wider recognition, simpler mental model, more explicit | Pre-implementation |
| 2026-06-14 | Frontend language = **TypeScript** confirmed | Type safety, industry standard, interview-impressive | Pre-implementation |
| 2026-06-14 | Backend layers: Router → Service → Repository → DB | Testable, single-responsibility | Round 5 Discovery |
| 2026-06-14 | Frontend: Zustand + React Query + CSS Modules + React Router v6 | Modern, minimal, interview-defensible | Round 5 Discovery |
| 2026-06-14 | Deployment: Railway (backend + PG) + Vercel (frontend) | Free tier, zero-config deploys | Round 5 Discovery |
| 2026-06-14 | Testing: pytest unit + integration tests; frontend not tested in v1 | Appropriate scope for assignment | Round 5 Discovery |
