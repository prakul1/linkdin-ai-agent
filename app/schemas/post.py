"""Post schemas — Phase 9.5: vibes mandatory."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.post import PostStyle, PostStatus
from app.schemas.attachment import AttachmentResponse
# Allowed vibe tags
ALLOWED_VIBES = {
    "funny", "serious", "motivational", "witty", "casual",
    "professional", "insightful", "emotional", "celebratory", "auto",
}
class PostGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=5, max_length=2000)
    style: PostStyle = Field(default=PostStyle.FORMAL)
    vibes: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Mandatory tone tags. Pick at least 1. Use ['auto'] to let AI decide.",
    )
    additional_instructions: Optional[str] = Field(default=None, max_length=500)
    attachment_ids: List[int] = Field(default_factory=list, max_length=8)
    @field_validator("vibes")
    @classmethod
    def validate_vibes(cls, v: List[str]) -> List[str]:
        v = [vibe.lower().strip() for vibe in v]
        invalid = [vibe for vibe in v if vibe not in ALLOWED_VIBES]
        if invalid:
            raise ValueError(
                f"Invalid vibes: {invalid}. Allowed: {sorted(ALLOWED_VIBES)}"
            )
        return v
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
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    topic: str
    style: PostStyle
    status: PostStatus
    content: Optional[str] = None
    created_at: datetime
    updated_at: datetime