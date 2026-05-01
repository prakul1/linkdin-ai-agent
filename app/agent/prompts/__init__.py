"""Prompt templates."""
from app.agent.prompts.system_prompt import SYSTEM_PROMPT
from app.agent.prompts.style_formal import FORMAL_STYLE
from app.agent.prompts.style_storytelling import STORYTELLING_STYLE
from app.agent.prompts.style_thought_leader import THOUGHT_LEADER_STYLE
__all__ = ["SYSTEM_PROMPT", "FORMAL_STYLE", "STORYTELLING_STYLE",
           "THOUGHT_LEADER_STYLE", "get_style_prompt"]
def get_style_prompt(style: str) -> str:
    mapping = {
        "formal": FORMAL_STYLE,
        "storytelling": STORYTELLING_STYLE,
        "thought_leadership": THOUGHT_LEADER_STYLE,
    }
    return mapping.get(style, FORMAL_STYLE)