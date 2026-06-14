# Splitly — Shared Expenses App

A shared expenses tracker built for flatmates. Track who paid what, split bills multiple ways, handle foreign currency, import messy spreadsheets, and see exactly who owes whom.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy (async) |
| Database | PostgreSQL |
| Auth | JWT (access + refresh tokens) |
| Frontend | React + Vite + TypeScript |
| Email | Resend |
| FX Rates | Frankfurter API (free, no key) |
| Backend Deploy | Railway |
| Frontend Deploy | Vercel |

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

---

### 1. Clone the repo

```bash
git clone https://github.com/your-username/splitly-spreetail.git
cd splitly-spreetail
```

---

### 2. Backend setup

```bash
cd backend
```

Create a `.env` file in `backend/` with:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/spreetail
ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/spreetail

SECRET_KEY=your-random-secret-key-at-least-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

RESEND_API_KEY=re_your_api_key_here
FRONTEND_URL=http://localhost:5173
```

Install dependencies and run migrations:

```bash
uv sync
uv run alembic upgrade head
```

Start the server:

```bash
uv run uvicorn app.main:app --reload
```

API docs available at: **http://localhost:8000/scalar**

---

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

App runs at: **http://localhost:5173**

---

## Importing the CSV

1. Log in and create a group
2. Add all flatmates as members (Aisha, Rohan, Priya, Meera, Dev, Sam)
3. Set Meera's `left_at` to March 31, 2026 (via the group leave flow)
4. Go to **Import** → upload `Expenses Export.csv`
5. The app will return a full import report listing every anomaly and what was done

> The import requires admin role on the group.

---

## Running Tests

```bash
cd backend
uv run pytest
```

---

## Project Structure

```
splitly-spreetail/
├── backend/
│   ├── app/
│   │   ├── core/          # security, email, FX
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic request/response
│   │   ├── repositories/  # DB queries (no business logic)
│   │   ├── services/      # Business logic
│   │   └── routers/       # HTTP routes
│   ├── alembic/           # Database migrations
│   └── pyproject.toml
├── frontend/
│   └── src/
├── SCOPE.md       # Anomaly log + DB schema
├── DECISIONS.md   # Engineering decision log
├── AI_USAGE.md    # AI tool usage log
└── README.md
```

---

## AI Tool Used

**Antigravity (Google DeepMind)** — used as a pair programming assistant throughout development. See [AI_USAGE.md](./AI_USAGE.md) for full details including cases where AI output was wrong and had to be corrected.
