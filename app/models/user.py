"""
User model.
Single user (you) for now, multi-user-ready for later.
"""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from app.models.base import Base, TimestampMixin
class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # LinkedIn OAuth tokens (encrypted in production — TODO Phase 9)
    linkedin_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_user_urn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # User preferences
    default_style: Mapped[str] = mapped_column(String(50), default="formal", nullable=False)
    # Relationships
    posts: Mapped[List["Post"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    token_usages: Mapped[List["TokenUsage"]] = relationship(back_populates="user")
    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"