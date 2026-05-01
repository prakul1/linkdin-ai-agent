"""SAFETY_CHECK node — rule-based, no LLM call."""
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agent.state import AgentState
from app.utils.safety_rules import run_all_safety_checks
from app.utils.logger import logger
def safety_node(state: AgentState, db: Session) -> Dict[str, Any]:
    draft = state.get("draft_content", "")
    result = run_all_safety_checks(draft)
    logger.info(
        f"[SAFETY] passed={result['passed']} score={result['score']} "
        f"issues={len(result['issues'])}"
    )
    if result["issues"]:
        for issue in result["issues"]:
            logger.warning(f"  - {issue}")
    return {
        "safety_passed": result["passed"],
        "safety_score": result["score"],
        "safety_issues": result["issues"],
    }