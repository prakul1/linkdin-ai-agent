"""Auth-related schemas (OAuth flow)."""
from typing import Optional
from pydantic import BaseModel
class LinkedInAuthURLResponse(BaseModel):
    auth_url: str
    state: str
class LinkedInConnectionStatus(BaseModel):
    connected: bool
    linkedin_user_urn: Optional[str] = None
    expires_in_message: Optional[str] = None
class ManualPostInfo(BaseModel):
    post_id: int
    content: str
    hashtags: Optional[str] = None
    instructions: str