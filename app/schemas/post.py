"""Post schemas — request validation and response shaping."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.post import PostStyle, PostStatus
from app.schemas.attachment import AttachmentResponse
class PostGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=5, max_length=2000)
    style: PostStyle = Field(default=PostStyle.FORMAL)
    additional_instructions: Optional[str] = Field(default=None, max_length=500)
class PostUpdateRequest(BaseModel):
    content: Optional[str] = Field(default=None, max_length=5000)
    hashtags: Optional[str] = Field(default=None, max_length=500)
class PostRejectRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)
class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())    
    id: int
    user_id: int
    topic: str
    style: PostStyle
    status: PostStatus
    content: Optional[str] = None
    hashtags: Optional[str] = None
    model_used: Optional[str] = None
    safety_score: Optional[int] = None
    user_edited: bool
    rejection_reason: Optional[str] = None
    generation_attempts: int
    attachments: List[AttachmentResponse] = []
    created_at: datetime
    updated_at: datetime
class PostListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic: str
    style: PostStyle
    status: PostStatus
    content: Optional[str] = None
    created_at: datetime
    updated_at: datetime