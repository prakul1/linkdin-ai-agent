"""
Schedule model — when and how to post.
"""
import enum
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.models.base import Base, TimestampMixin
class ScheduleStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
class Schedule(Base, TimestampMixin):
    __tablename__ = "schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    status: Mapped[ScheduleStatus] = mapped_column(
        SQLEnum(ScheduleStatus), default=ScheduleStatus.PENDING, index=True, nullable=False
    )
    # Retry mechanism
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(default=3, nullable=False)
    # Outcome
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    linkedin_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Relationships
    post: Mapped["Post"] = relationship(back_populates="schedules")
    def __repr__(self) -> str:
        return f"<Schedule id={self.id} at={self.scheduled_at} status={self.status}>"