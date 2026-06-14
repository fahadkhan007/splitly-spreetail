# Splitly — Advanced Shared Expenses Tracker

Splitly is a beautiful, robust, full-stack application designed to take the friction out of shared finances. Whether you're tracking apartment bills, organizing a group vacation, or importing messy historical spreadsheets, Splitly handles the math so you don't have to.

It features advanced capabilities including **live foreign exchange (FX) rates**, **smart debt simplification algorithms**, **email invitations**, and a **robust CSV data import engine** designed to handle real-world, anomalous data.

---

## ✨ Features

### 🔐 Authentication & Security
- Secure user registration and login.
- Access and Refresh token architecture using JWTs.
- Email verification hooks using Resend.

### 👥 Group Management
- **Create & Configure:** Spin up groups for trips, apartments, or events, and define a base currency for the group.
- **Role-based Access:** Group Admins can invite new members via email, remove members, or close the group entirely.
- **Pending Invites:** Admins can track pending email invitations. Invited users receive a secure link to instantly join the group.

### 💸 Expense Tracking & Splits
- **Multiple Split Methods:** Split expenses *Equally*, by *Exact Amounts*, by *Percentages*, or by *Shares*.
- **Foreign Currency Support:** Traveling? Add an expense in EUR, GBP, or INR. Splitly automatically queries historical or live FX rates (via the Frankfurter API) and converts the cost into your group's base currency!
- **Unified Activity Feed:** A chronological ledger of all group activity. Admins and payers can **Edit** or **Delete** expenses seamlessly.

### 🤝 Settling Up & Balances
- **Smart Debt Simplification:** Splitly's engine calculates everyone's net balance and generates an optimized "Who Owes Whom" list, minimizing the total number of transactions required to settle the group.
- **Record Payments:** Easily log a cash payment to settle a debt.
- **Voiding:** Made a mistake? Settlements can be voided to instantly restore the previous balances.

### 📊 Analytics & Reporting
- **Interactive Dashboards:** View total group spend, category breakdowns (e.g., Groceries vs Utilities), and monthly spending trends.
- **Member Summaries:** See exactly how much each person has paid vs. how much their share of the costs were.

### 📥 Advanced CSV Imports
- **Smart Parsing:** Upload legacy spreadsheets. Splitly cleanses the data, maps messy names to actual users, normalizes dates, and handles missing categories.
- **Detailed Audits:** Every import generates a detailed report showing exactly what rows were successfully imported, what warnings were triggered (e.g., "Assumed USD currency"), and any anomalies detected.

---

## 🛠️ Technology Stack

Splitly leverages a modern, high-performance tech stack:

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI + Python 3.11+ |
| **Database ORM** | SQLAlchemy 2.0 (Fully Async) |
| **Database** | PostgreSQL |
| **Auth** | JWT (access + refresh tokens) |
| **Frontend UI** | React 19 + TypeScript + Vite |
| **State Management** | React Context + React Router v7 |
| **Styling** | Vanilla CSS (Custom Design System, Glassmorphism, CSS Variables) |
| **Email Delivery** | Resend API |
| **FX Rates** | Frankfurter API (Free, open-source FX data) |
| **Testing** | Pytest |

---

## 🚀 Local Development Setup

Follow these steps to run Splitly locally on your machine.

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **[uv](https://docs.astral.sh/uv/)** (Fast Python package manager)

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

Create a `.env` file in the `backend/` directory with your PostgreSQL credentials:
```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/spreetail
ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/spreetail

SECRET_KEY=your-random-secret-key-at-least-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

RESEND_API_KEY=re_your_api_key_here
FRONTEND_URL=http://localhost:5173
```

Install dependencies and run database migrations:
```bash
uv sync
uv run alembic upgrade head
```

Start the FastAPI server:
```bash
uv run uvicorn app.main:app --reload
```
*The backend API will be running at `http://localhost:8000`.*
*Interactive API Docs available at `http://localhost:8000/scalar`.*

### 3. Frontend Setup
Open a new terminal window and navigate to the frontend directory:
```bash
cd frontend
```

Install Node dependencies:
```bash
npm install
```

Start the Vite development server:
```bash
npm run dev
```
*The frontend React app will be running at `http://localhost:5173`.*

---

## 📂 Project Architecture

```text
splitly-spreetail/
├── backend/
│   ├── alembic/           # Database schema migrations
│   ├── app/
│   │   ├── core/          # Security, Email clients, FX API integration
│   │   ├── models/        # SQLAlchemy database models
│   │   ├── schemas/       # Pydantic schemas for API validation
│   │   ├── repositories/  # Database queries (Repository pattern)
│   │   ├── services/      # Core business logic (Imports, Balances)
│   │   └── routers/       # FastAPI HTTP endpoints
│   └── tests/             # Pytest test suite
├── frontend/
│   ├── src/
│   │   ├── api/           # Typed Axios API clients matching backend schemas
│   │   ├── components/    # Reusable UI components and Modals
│   │   ├── context/       # Global Auth state
│   │   ├── layouts/       # Main sidebar/navigation layout
│   │   ├── pages/         # Full-page views (Dashboard, Group, Settings, Reports)
│   │   └── App.tsx        # React Router configuration
│   └── index.css          # Design system variables and core styles
├── SCOPE.md               # Original project requirements
├── DECISIONS.md           # Engineering decision log
└── AI_USAGE.md            # AI tool usage log
```

---

## 🧪 Running Tests
The backend includes a comprehensive test suite covering the core logic, especially the complex CSV import anomaly detection and FX conversions.

```bash
cd backend
uv run pytest
```

---

## 📈 Import Engine Testing Guide
To test the robust CSV import engine using the provided sample data:
1. Log into the local app and create a new group.
2. Go to **Group Settings** and invite all flatmates (Aisha, Rohan, Priya, Meera, Dev, Sam) and ensure they are members.
3. Click **Import CSV** in the left sidebar and upload the legacy `Expenses Export.csv`.
4. Splitly will process the file, normalize the currencies, flag anomalies, and return a beautiful, detailed Import Report outlining the success of the operation.

---

*Built with precision and an eye for design.*
