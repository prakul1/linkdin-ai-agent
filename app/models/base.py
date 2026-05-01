"""
SQLAlchemy declarative base.
All models inherit from Base — gives them common columns like id and timestamps.
"""
from datetime import datetime
from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
class Base(DeclarativeBase):
    """Base class for all DB models."""
    pass
class TimestampMixin:
    """
    Mixin that adds created_at and updated_at to any model.
    Why a mixin? DRY principle — write once, use everywhere.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )