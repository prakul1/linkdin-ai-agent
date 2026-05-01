"""
Initialize database: create tables and seed default user.
"""
from loguru import logger
from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal
from app.models import Base, User
def create_tables() -> None:
    """Create all tables defined in models."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created.")
def seed_default_user(db: Session) -> User:
    """Create your default user if not exists."""
    user = db.query(User).filter(User.email == "you@example.com").first()
    if user:
        logger.info(f"Default user already exists: {user}")
        return user
    user = User(
        email="you@example.com",
        name="Default User",
        default_style="formal",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created default user: {user}")
    return user
def init_db() -> None:
    """Full initialization."""
    create_tables()
    db = SessionLocal()
    try:
        seed_default_user(db)
    finally:
        db.close()
if __name__ == "__main__":
    init_db()