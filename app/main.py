"""
FastAPI entry point. Minimal version to verify setup.
We'll add real routes in Phase 4.
"""
from fastapi import FastAPI
from app.config import settings
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)
@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "status": "running",
        "env": settings.app_env,
    }
@app.get("/health")
def health():
    """Used by Docker healthcheck and uptime monitors."""
    return {"status": "healthy"}