"""
Post model — the core entity.
"""
import enum
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from app.models.base import Base, TimestampMixin
class PostStatus(str, enum.Enum):
    """Post lifecycle states. str-enum so values are JSON-serializable."""
    DRAFT = "draft"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    REJECTED = "rejected"
class PostStyle(str, enum.Enum):
    """Available writing styles."""
    FORMAL = "formal"
    STORYTELLING = "storytelling"
    THOUGHT_LEADERSHIP = "thought_leadership"
class Post(Base, TimestampMixin):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    # User input
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    style: Mapped[PostStyle] = mapped_column(
        SQLEnum(PostStyle), default=PostStyle.FORMAL, nullable=False
    )
    # Generated output
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Lifecycle
    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus), default=PostStatus.DRAFT, index=True, nullable=False
    )
    # Generation metadata
    model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    generation_attempts: Mapped[int] = mapped_column(default=1, nullable=False)
    safety_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    # User feedback
    user_edited: Mapped[bool] = mapped_column(default=False, nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Relationships
    user: Mapped["User"] = relationship(back_populates="posts")
    attachments: Mapped[List["Attachment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    schedules: Mapped[List["Schedule"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    token_usages: Mapped[List["TokenUsage"]] = relationship(back_populates="post")
    def __repr__(self) -> str:
        return f"<Post id={self.id} status={self.status} style={self.style}>"