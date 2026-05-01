"""LangGraph agent definition — Phase 7: accepts attachment_context."""
from functools import partial
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session
from app.agent.state import AgentState
from app.agent.nodes import retrieve_node, generate_node, safety_node, refine_node
from app.utils.logger import logger
MAX_GENERATION_ATTEMPTS = 2
def _safety_router(state):
    passed = state.get("safety_passed", False)
    attempts = state.get("generation_attempts", 1)
    if passed:
        return "refine"
    if attempts < MAX_GENERATION_ATTEMPTS:
        return "generate"
    return "refine"
def build_agent_graph(db):
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", partial(retrieve_node, db=db))
    graph.add_node("generate", partial(generate_node, db=db))
    graph.add_node("safety", partial(safety_node, db=db))
    graph.add_node("refine", partial(refine_node, db=db))
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "safety")
    graph.add_conditional_edges("safety", _safety_router,
                                {"generate": "generate", "refine": "refine"})
    graph.add_edge("refine", END)
    return graph.compile()
def run_agent(
    db, user_id, post_id, topic, style,
    additional_instructions=None,
    attachment_context=None,
):
    logger.info(f"[AGENT] Starting for post_id={post_id}, style={style}")
    if attachment_context:
        logger.info(f"[AGENT] With {len(attachment_context)} attachment(s)")
    initial_state = {
        "user_id": user_id,
        "post_id": post_id,
        "topic": topic,
        "style": style,
        "additional_instructions": additional_instructions,
        "attachment_context": attachment_context or [],
        "generation_attempts": 0,
    }
    app = build_agent_graph(db)
    final_state = app.invoke(initial_state)
    return final_state