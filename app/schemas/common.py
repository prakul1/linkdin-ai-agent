"""Shared schemas used across endpoints."""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field
T = TypeVar("T")
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None