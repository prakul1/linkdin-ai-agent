"""Upload-related schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from app.models.attachment import AttachmentType
class LinkUploadRequest(BaseModel):
    url: HttpUrl
    post_id: Optional[int] = None
class FileUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    file_type: AttachmentType
    original_filename: Optional[str] = None
    url: Optional[str] = None
    file_size: Optional[int] = None
    extracted_text_preview: str = ""
    extracted_text_length: int = 0
    created_at: datetime
class AttachPostRequest(BaseModel):
    attachment_ids: List[int] = Field(..., min_length=1, max_length=5)