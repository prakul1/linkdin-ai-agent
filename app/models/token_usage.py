"""
TokenUsage model — track every LLM call for cost monitoring.
This is your $6 budget tracker!
"""
from sqlalchemy import String, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.models.base import Base, TimestampMixin
class TokenUsage(Base, TimestampMixin):
    __tablename__ = "token_usage"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    post_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("posts.id"), index=True, nullable=True
    )
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    tokens_input: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # Relationships
    user: Mapped["User"] = relationship(back_populates="token_usages")
    post: Mapped[Optional["Post"]] = relationship(back_populates="token_usages")
    def __repr__(self) -> str:
        return f"<TokenUsage model={self.model} tokens={self.tokens_input + self.tokens_output} cost=${self.cost_usd:.4f}>"