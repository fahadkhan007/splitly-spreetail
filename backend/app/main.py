# app/main.py
#
# This is the entry point for the FastAPI application.
# All routers (auth, groups, expenses, etc.) will be registered here.
#
# To run the server:
#   uvicorn app.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


# ── CREATE THE APP ───────────────────────────────────────────────
app = FastAPI(
    title="Splitly API",
    description="Shared expenses application — backend API",
    version="1.0.0",
)


# ── CORS MIDDLEWARE ──────────────────────────────────────────────
# Allows the React frontend (running on a different port) to call this API.
# In production, FRONTEND_URL will be the Vercel deployment URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,     # Needed for HttpOnly cookies (refresh tokens)
    allow_methods=["*"],        # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],        # Allow Authorization header and others
)


# ── HEALTH CHECK ─────────────────────────────────────────────────
# A simple route to confirm the server is running.
# Visit http://localhost:8000/health in your browser to test.
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Splitly API is running"}


@app.get("/")
async def get_app():
    return {"message": "Splitly API is running"}
    
# ── ROUTERS ──────────────────────────────────────────────────────
# Routers will be added here as we build each section.
# Example (uncomment when ready):
# from app.routers import auth, groups, expenses
# app.include_router(auth.router, prefix="/auth", tags=["auth"])
# app.include_router(groups.router, prefix="/groups", tags=["groups"])
