"""
FastAPI entry point with DB initialization on startup.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from app.config import settings
from app.db.init_db import init_db
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on startup and shutdown."""
    logger.info(f"Starting {settings.app_name}")
    init_db()
    yield
    logger.info("Shutting down")
app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    debug=settings.debug,
    lifespan=lifespan,
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
    return {"status": "healthy"}