"""Agent state — Phase 7: Added attachment_context."""
from typing import TypedDict, List, Optional, Dict, Any
from app.models.post import PostStyle
class AgentState(TypedDict, total=False):
    user_id: int
    post_id: int
    topic: str
    style: PostStyle
    additional_instructions: Optional[str]
    attachment_context: List[Dict[str, str]]   # NEW
    similar_posts: List[Dict[str, Any]]
    avoid_phrases: List[str]
    draft_content: str
    generation_attempts: int
    safety_passed: bool
    safety_score: int
    safety_issues: List[str]
    final_content: str
    hashtags: str
    error: Optional[str]