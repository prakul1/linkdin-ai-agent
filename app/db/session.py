"""
Database engine and session factory.
SQLite for local, swap to Postgres in cloud (1-line change).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import settings
# SQLite needs this special arg; Postgres doesn't
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a DB session per request.
    Auto-closes after request (even on errors).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()