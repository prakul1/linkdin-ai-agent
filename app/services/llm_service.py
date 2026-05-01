"""LLM service — wraps OpenAI chat completions with cost tracking."""
from typing import List, Dict, Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from app.config import settings
from app.models.token_usage import TokenUsage
from app.utils.pricing import calculate_cost
from app.utils.token_counter import count_tokens
from app.utils.logger import logger
class LLMService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens_per_request
    def chat(self, messages, user_id=None, post_id=None, operation="chat",
             temperature=0.7, max_tokens=None):
        max_t = max_tokens or self.max_tokens
        input_text = " ".join(m["content"] for m in messages)
        input_tokens = count_tokens(input_text, self.model)
        logger.debug(f"LLM call: {input_tokens} input tokens, op={operation}")
        response = self.client.chat.completions.create(
            model=self.model, messages=messages,
            temperature=temperature, max_tokens=max_t,
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        if self.db and user_id:
            self._track_usage(user_id, post_id, usage.prompt_tokens,
                              usage.completion_tokens, operation)
        return content
    def _track_usage(self, user_id, post_id, tokens_in, tokens_out, operation):
        cost = calculate_cost(self.model, tokens_in, tokens_out)
        usage = TokenUsage(
            user_id=user_id, post_id=post_id, model=self.model,
            operation=operation, tokens_input=tokens_in,
            tokens_output=tokens_out, cost_usd=cost,
        )
        self.db.add(usage)
        self.db.commit()
        logger.info(f"LLM cost: ${cost:.6f} | in={tokens_in} out={tokens_out} | op={operation}")