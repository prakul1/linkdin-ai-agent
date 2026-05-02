"""FastAPI entry point — Phase 9: LinkedIn integration enabled."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.init_db import init_db
from app.utils.logger import logger
from app.utils.file_utils import ensure_upload_dir
from app.services.scheduler_service import SchedulerService
from app.api import (
    routes_posts, routes_approval, routes_rag,
    routes_uploads, routes_schedule, routes_auth,
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}")
    init_db()
    ensure_upload_dir()
    SchedulerService.start()
    yield
    SchedulerService.shutdown()
app = FastAPI(
    title=settings.app_name,
    version="0.9.0",
    debug=settings.debug,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routes_posts.router)
app.include_router(routes_approval.router)
app.include_router(routes_rag.router)
app.include_router(routes_uploads.router)
app.include_router(routes_schedule.router)
app.include_router(routes_auth.router)
@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "status": "running",
        "env": settings.app_env,
        "docs": "/docs",
    }
@app.get("/health")
def health():
    return {"status": "healthy"}