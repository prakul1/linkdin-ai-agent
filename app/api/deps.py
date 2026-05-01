"""Shared dependencies for FastAPI routes."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.services.post_service import PostService
def get_current_user(db: Session = Depends(get_db)) -> User:
    """TEMPORARY: Returns the default seeded user. Replace with JWT auth later."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user not found. Restart app to re-seed.",
        )
    return user
def get_post_service(db: Session = Depends(get_db)) -> PostService:
    return PostService(db)