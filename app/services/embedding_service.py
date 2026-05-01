"""Embedding service — wraps OpenAI embeddings + tracks cost."""
from typing import List, Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from app.config import settings
from app.models.token_usage import TokenUsage
from app.utils.pricing import calculate_cost
from app.utils.token_counter import count_tokens
from app.utils.logger import logger
class EmbeddingService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
    def embed_text(
        self,
        text: str,
        user_id: Optional[int] = None,
        post_id: Optional[int] = None,
        operation: str = "embed",
    ) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        tokens = count_tokens(text, model=self.model)
        logger.debug(f"Embedding {tokens} tokens with {self.model}")
        response = self.client.embeddings.create(model=self.model, input=text)
        embedding = response.data[0].embedding
        if self.db and user_id:
            self._track_usage(
                user_id=user_id, post_id=post_id, tokens_in=tokens, operation=operation
            )
        return embedding
    def embed_batch(
        self,
        texts: List[str],
        user_id: Optional[int] = None,
        operation: str = "embed_batch",
    ) -> List[List[float]]:
        if not texts:
            return []
        total_tokens = sum(count_tokens(t, model=self.model) for t in texts)
        logger.debug(f"Batch embedding {len(texts)} texts, {total_tokens} tokens")
        response = self.client.embeddings.create(model=self.model, input=texts)
        embeddings = [d.embedding for d in response.data]
        if self.db and user_id:
            self._track_usage(
                user_id=user_id, post_id=None, tokens_in=total_tokens, operation=operation
            )
        return embeddings
    def _track_usage(self, user_id, post_id, tokens_in, operation):
        cost = calculate_cost(self.model, tokens_in, 0)
        usage = TokenUsage(
            user_id=user_id,
            post_id=post_id,
            model=self.model,
            operation=operation,
            tokens_input=tokens_in,
            tokens_output=0,
            cost_usd=cost,
        )
        self.db.add(usage)
        self.db.commit()
        logger.info(f"Embedding cost: ${cost:.6f} ({tokens_in} tokens)")