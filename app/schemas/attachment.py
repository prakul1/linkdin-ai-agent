"""Attachment schemas (full upload handling in Phase 7)."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.attachment import AttachmentType
class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    file_type: AttachmentType
    original_filename: Optional[str] = None
    url: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime