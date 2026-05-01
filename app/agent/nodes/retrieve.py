"""RETRIEVE node — fetches similar past posts via RAG."""
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agent.state import AgentState
from app.services.rag_service import RAGService
from app.utils.logger import logger
def retrieve_node(state: AgentState, db: Session) -> Dict[str, Any]:
    logger.info(f"[RETRIEVE] topic='{state['topic'][:60]}...'")
    rag = RAGService(db=db)
    similar = rag.retrieve_similar(
        query_text=state["topic"], user_id=state["user_id"], top_k=3,
    )
    avoid_phrases = []
    for p in similar:
        content = p.get("content", "")
        first_line = content.split("\n")[0][:100] if content else ""
        if first_line:
            avoid_phrases.append(first_line)
    logger.info(f"[RETRIEVE] Found {len(similar)} similar posts")
    return {"similar_posts": similar, "avoid_phrases": avoid_phrases}