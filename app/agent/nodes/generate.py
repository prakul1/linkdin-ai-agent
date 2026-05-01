"""GENERATE node — Phase 7: includes attachment context."""
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT, get_style_prompt
from app.services.llm_service import LLMService
from app.utils.logger import logger
MAX_ATTACHMENT_CHARS_IN_PROMPT = 1500
def _build_user_prompt(state):
    style_val = state["style"].value if hasattr(state["style"], "value") else state["style"]
    style_guide = get_style_prompt(style_val)
    parts = [style_guide, ""]
    attachments = state.get("attachment_context", [])
    if attachments:
        parts.append("REFERENCE MATERIAL (use this to enrich the post, but write in your own words):")
        for i, att in enumerate(attachments, 1):
            kind = att.get("type", "doc").upper()
            source = att.get("source", "")
            text = att.get("text", "")[:MAX_ATTACHMENT_CHARS_IN_PROMPT]
            header = f"\n--- {kind} {i}"
            if source:
                header += f" ({source})"
            header += " ---"
            parts.append(header)
            parts.append(text)
        parts.append("")
    avoid = state.get("avoid_phrases", [])
    if avoid:
        parts.append("YOUR PAST OPENING LINES (do NOT reuse):")
        for line in avoid[:3]:
            parts.append(f"- {line}")
        parts.append("")
    extra = state.get("additional_instructions")
    if extra:
        parts.append(f"ADDITIONAL INSTRUCTIONS: {extra}")
        parts.append("")
    parts.append(f"TOPIC: {state['topic']}")
    parts.append("")
    parts.append("Write the LinkedIn post now.")
    return "\n".join(parts)
def generate_node(state: AgentState, db: Session) -> Dict[str, Any]:
    attempts = state.get("generation_attempts", 0) + 1
    logger.info(f"[GENERATE] Attempt #{attempts}")
    user_prompt = _build_user_prompt(state)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    temperature = min(0.7 + (0.1 * (attempts - 1)), 1.0)
    llm = LLMService(db=db)
    draft = llm.chat(
        messages=messages,
        user_id=state["user_id"],
        post_id=state.get("post_id"),
        operation=f"generate_attempt_{attempts}",
        temperature=temperature,
        max_tokens=600,
    )
    return {"draft_content": draft.strip(), "generation_attempts": attempts}