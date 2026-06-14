# app/main.py
#
# This is the entry point for the FastAPI application.
# All routers (auth, groups, expenses, etc.) will be registered here.
#
# To run the server:
#   uvicorn app.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference

from app.config import settings


# ── CREATE THE APP ───────────────────────────────────────────────
app = FastAPI(
    title="Splitly API",
    description="Shared expenses application — backend API",
    version="1.0.0",
    docs_url=None,     # disable default Swagger UI
    redoc_url=None,    # disable default ReDoc UI
)


# ── CORS MIDDLEWARE ──────────────────────────────────────────────
# Allows the React frontend (running on a different port) to call this API.
# In production, FRONTEND_URL will be the Vercel deployment URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "https://splitly-spreetail.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,     # Needed for HttpOnly cookies (refresh tokens)
    allow_methods=["*"],        # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],        # Allow Authorization header and others
)



@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Splitly API is running"}


@app.get("/")
async def get_app():
    return {"message": "Splitly API is running"}


# ── SCALAR DOCS ──────────────────────────────────────────────
# Beautiful API reference UI — visit http://localhost:8000/scalar
@app.get("/scalar", include_in_schema=False, response_class=HTMLResponse)
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        title="Splitly API",
    )
# ── ROUTERS ──────────────────────────────────────────────────────
# Each router handles a specific feature area.
# New routers will be added here as we build each section.
from app.routers import auth, users, groups, invitations, expenses, settlements, imports, reports

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(groups.router, prefix="/groups", tags=["Groups"])
app.include_router(invitations.router, tags=["Invitations"])
app.include_router(expenses.router, tags=["Expenses & Balances"])
app.include_router(settlements.router, tags=["Settlements"])
app.include_router(imports.router, tags=["CSV Import"])
app.include_router(reports.router, tags=["Reports"])



