"""
Attachment model — files/links associated with a post.
"""
import enum
from sqlalchemy import String, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.models.base import Base, TimestampMixin
class AttachmentType(str, enum.Enum):
    PDF = "pdf"
    IMAGE = "image"
    LINK = "link"
class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True, nullable=False)
    file_type: Mapped[AttachmentType] = mapped_column(SQLEnum(AttachmentType), nullable=False)
    # For files
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # For links
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Cached extracted text (saves money on re-processing!)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Relationships
    post: Mapped["Post"] = relationship(back_populates="attachments")
    def __repr__(self) -> str:
        return f"<Attachment id={self.id} type={self.file_type}>"