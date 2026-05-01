"""REFINE node — final polish: hooks, hashtags, formatting."""
import re
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agent.state import AgentState
from app.services.llm_service import LLMService
from app.utils.logger import logger
REFINE_PROMPT = """Polish this LinkedIn post:
1. Make the FIRST LINE a strong hook
2. Add line breaks for readability
3. Ensure 3-5 relevant hashtags at the END
4. Remove any hashtags from the middle
5. Keep the core message intact — don't rewrite, just polish
Return ONLY the polished post. No explanations.
POST:
{draft}
"""
def _extract_hashtags(text):
    tags = re.findall(r"#\w+", text)
    seen = set()
    unique = []
    for t in tags:
        if t.lower() not in seen:
            unique.append(t)
            seen.add(t.lower())
    return ", ".join(unique)
def refine_node(state: AgentState, db: Session) -> Dict[str, Any]:
    draft = state.get("draft_content", "")
    logger.info(f"[REFINE] Polishing draft ({len(draft)} chars)")
    llm = LLMService(db=db)
    polished = llm.chat(
        messages=[{"role": "user", "content": REFINE_PROMPT.format(draft=draft)}],
        user_id=state["user_id"],
        post_id=state.get("post_id"),
        operation="refine",
        temperature=0.4,
        max_tokens=600,
    )
    polished = polished.strip()
    hashtags = _extract_hashtags(polished)
    logger.info(f"[REFINE] Final: {len(polished)} chars")
    return {"final_content": polished, "hashtags": hashtags}