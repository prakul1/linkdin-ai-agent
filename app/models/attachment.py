"""Attachment model — supports both context and media-to-post."""
import enum
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.models.base import Base, TimestampMixin
class AttachmentType(str, enum.Enum):
    PDF = "pdf"
    IMAGE = "image"
    LINK = "link"
    VIDEO = "video"   # NEW Phase 9.5
class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True, nullable=False)
    file_type: Mapped[AttachmentType] = mapped_column(SQLEnum(AttachmentType), nullable=False)
    # File metadata
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # NEW
    # For links
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Cached extracted text (context attachments only)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # NEW Phase 9.5: True = posted with content, False = LLM context only
    is_media: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    post: Mapped["Post"] = relationship(back_populates="attachments")
    def __repr__(self) -> str:
        return f"<Attachment id={self.id} type={self.file_type} is_media={self.is_media}>"