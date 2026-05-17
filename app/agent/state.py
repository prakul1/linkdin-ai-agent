"""Agent state — Phase 9.5: Added vibes."""
from typing import TypedDict, List, Optional, Dict, Any
from app.models.post import PostStyle
class AgentState(TypedDict, total=False):
    user_id: int
    post_id: int
    topic: str
    style: PostStyle
    vibes: List[str]                          # NEW Phase 9.5
    additional_instructions: Optional[str]
    attachment_context: List[Dict[str, str]]
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