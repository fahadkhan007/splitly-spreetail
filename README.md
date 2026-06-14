<div align="center">
  <img src="frontend/public/favicon.png" width="100" height="100" alt="Splitly Logo" />
  <h1>Splitly</h1>
  <p><strong>Advanced Shared Finances, Simplified.</strong></p>
  <p>A full-stack, enterprise-grade application for tracking shared expenses, seamlessly handling foreign currency conversions, smart debt simplification, and legacy data migration.</p>
</div>

---

## 📖 Table of Contents
1. [Core Features](#-core-features)
2. [Deep Dive: System Architecture](#-deep-dive-system-architecture)
3. [Deep Dive: Debt Simplification Engine](#-deep-dive-debt-simplification-engine)
4. [Deep Dive: CSV Import Engine](#-deep-dive-csv-import-engine)
5. [Technology Stack](#️-technology-stack)
6. [Local Development Setup](#-local-development-setup)
7. [Testing](#-testing)
8. [Project Structure](#-project-structure)

---

## ✨ Core Features

### 🔐 Authentication & Identity
- **Secure Sessions**: Utilizes a robust JWT architecture (short-lived access tokens, long-lived HTTP-only refresh tokens) built with FastAPI security utilities.
- **Email Verification**: Integration with the Resend API ensures users must verify their email addresses before establishing groups.

### 👥 Group & Member Management
- **Role-Based Access Control (RBAC)**: Distinct permissions for `ADMIN` vs `MEMBER`. Only admins can invite users, remove users, update group settings, or close groups.
- **Asynchronous Invitations**: Admins can invite unregistered flatmates via email. Splitly tracks pending invites and provides secure, tokenized `Accept Invite` magic links.

### 💸 Multi-Currency Expense Tracking
- **Split Mechanics**: Core support for dividing bills *Equally*, by *Exact Amounts*, by *Percentages*, or by *Shares* (e.g., "John pays 2 shares, Jane pays 1").
- **Live Foreign Exchange (FX)**: If your group's base currency is USD, but an expense is recorded in GBP, the backend automatically queries the **Frankfurter API** to fetch the historical or current FX rate and normalizes the debt ledger.
- **Unified Activity Feed**: A central ledger showcasing chronological expenses and cash settlements. Supports inline editing, soft-deletion of expenses, and voiding of settlements.

---

## 🏛️ Deep Dive: System Architecture

Splitly is built around a decoupled client-server architecture emphasizing type safety, asynchronous processing, and a strict separation of concerns.

### Backend (FastAPI + Asyncpg)
The backend completely avoids synchronous blocking. It uses `asyncpg` combined with SQLAlchemy 2.0's `AsyncSession` to achieve extremely high throughput. The architecture strictly follows the **Repository Pattern**:
- **Routers**: FastAPI endpoints that handle HTTP parsing and response serialization (Pydantic).
- **Services**: Pure business logic (e.g., calculating debts, verifying import rows, fetching FX rates).
- **Repositories**: Isolated database I/O, ensuring SQL queries never leak into business logic.

### Frontend (React + Vite)
The frontend utilizes a lightweight, highly responsive architecture:
- **State Management**: Combines React Context (for global Auth state) and localized component state, minimizing unnecessary re-renders.
- **Design System**: A completely custom, dependency-free CSS design system using CSS Variables, modern Glassmorphism aesthetics, and responsive flex/grid layouts. Tailwind and heavy UI libraries were intentionally avoided to ensure a lean bundle size.

---

## 🧠 Deep Dive: Debt Simplification Engine

One of Splitly's standout technical features is its **Smart Debt Simplification Engine**. 

When multiple flatmates owe each other money (e.g., A owes B $10, B owes C $20, C owes A $5), a naive system forces everyone to make separate transactions. Splitly calculates the *net balance* of every user and computes an optimized matrix of settlements.

**How it works:**
1. Aggregate the total amount paid vs. the total amount owed for every user.
2. Determine each user's `net_balance` (Positive = they are owed money; Negative = they owe money).
3. Split users into two pools: `Debtors` (negative balance) and `Creditors` (positive balance).
4. Iteratively match the largest Debtor with the largest Creditor to resolve balances, generating a concise list of "Suggested Payments" (e.g., "A simply pays C $5").

---

## 📥 Deep Dive: CSV Import Engine

Migrating data from messy, legacy spreadsheets (like Splitwise exports) is historically painful. Splitly features a robust backend pipeline designed to handle highly anomalous CSV data.

**The Import Pipeline:**
1. **Header Normalization:** Flattens headers, strips whitespace, and identifies critical columns regardless of case (e.g., identifying `Cost` vs `Amount`).
2. **Date Parsing Matrix:** Falls back through multiple Regex and `strptime` patterns to parse dates (`MM/DD/YYYY`, `DD-MM-YY`, etc.).
3. **Fuzzy Identity Matching:** If the CSV says "Aisha S.", but the database user is "Aisha Sharma", the engine uses fuzzy string matching to align the records.
4. **Anomaly Flagging:** The engine does not fail on bad data. Instead, it flags anomalies (e.g., "Assumed default currency USD", "Skipped row due to unparseable cost") and compiles a beautiful, actionable JSON **Import Report** for the user to review.

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend Framework** | FastAPI + Python 3.11+ |
| **Database ORM** | SQLAlchemy 2.0 (Fully Async via asyncpg) |
| **Database** | PostgreSQL 14+ |
| **Authentication** | JWT (PyJWT), Passlib (Bcrypt) |
| **Frontend Framework** | React 19 + TypeScript |
| **Frontend Bundler** | Vite |
| **Routing** | React Router v7 |
| **Email Delivery** | Resend API |
| **External FX API** | Frankfurter API (Open-source foreign exchange rates) |
| **Testing** | Pytest, HTTPX |

---

## 🚀 Local Development Setup

Follow these steps to run the Splitly application locally on your machine.

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **[uv](https://docs.astral.sh/uv/)** (Extremely fast Python package manager written in Rust)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/splitly-spreetail.git
cd splitly-spreetail
```

### 2. Backend Setup
Navigate to the backend directory:
```bash
cd backend
```

Create a `.env` file in the `backend/` directory with your database credentials:
```env
# Database Connections
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/spreetail
ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/spreetail

# Security
SECRET_KEY=your-random-secret-key-at-least-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# External APIs
RESEND_API_KEY=re_your_api_key_here
FRONTEND_URL=http://localhost:5173
```

Install dependencies using `uv` and run the database migrations:
```bash
uv sync
uv run alembic upgrade head
```

Start the FastAPI development server:
```bash
uv run uvicorn app.main:app --reload
```
- **Local API:** `http://localhost:8000`
- **Interactive Swagger Docs (Scalar):** `http://localhost:8000/scalar`

### 3. Frontend Setup
Open a new terminal window and navigate to the frontend directory:
```bash
cd frontend
```

Install Node dependencies and start the Vite development server:
```bash
npm install
npm run dev
```
- **Local UI:** `http://localhost:5173`

---

## 🧪 Testing

The backend includes a comprehensive `pytest` suite validating the core logic, especially testing the complexity of the CSV import engine and the mathematical accuracy of the debt simplification algorithm.

```bash
cd backend
uv run pytest -v
```

---

## 📂 Project Structure

```text
splitly-spreetail/
├── backend/
│   ├── alembic/           # Database schema migrations
│   ├── app/
│   │   ├── core/          # Security, Email clients, FX API integration
│   │   ├── models/        # SQLAlchemy database models
│   │   ├── schemas/       # Pydantic schemas for API validation
│   │   ├── repositories/  # Database queries (Repository pattern)
│   │   ├── services/      # Core business logic (Imports, Balances, Algorithms)
│   │   └── routers/       # FastAPI HTTP endpoints
│   └── tests/             # Pytest test suite
├── frontend/
│   ├── public/            # Static assets (Favicons)
│   ├── src/
│   │   ├── api/           # Typed Axios API clients matching backend schemas
│   │   ├── components/    # Reusable UI components and Modals
│   │   ├── context/       # Global React Context providers
│   │   ├── layouts/       # Main sidebar/navigation wrapper
│   │   ├── pages/         # Full-page routing views
│   │   └── App.tsx        # React Router v7 configuration
│   └── index.css          # Design system variables and core styles
├── SCOPE.md               # Original project requirements and initial schema
├── DECISIONS.md           # Engineering decision log
└── AI_USAGE.md            # AI tool usage log
```
