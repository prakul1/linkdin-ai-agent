"""RAG-related schemas for inspect/debug endpoints."""
from typing import List, Optional
from pydantic import BaseModel, Field
class SimilarPostItem(BaseModel):
    post_id: int
    content: str
    topic: str
    style: str
    similarity: float = Field(..., ge=0.0, le=1.0)
class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)
    style_filter: Optional[str] = None
class RetrieveResponse(BaseModel):
    query: str
    results: List[SimilarPostItem]
class RepetitionCheckRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=5000)
    threshold: float = Field(default=0.85, ge=0.0, le=1.0)
class RepetitionCheckResponse(BaseModel):
    is_repetitive: bool
    max_similarity: float
    similar_post_id: Optional[int] = None
class RAGStatsResponse(BaseModel):
    total_documents: int
    collection_name: str
    persist_dir: str

class SafetyCheckRequest(BaseModel):
    '''test the safety layer directly with arbitrary text.'''
    content : str = Field(...,min_length=1,max_length=5000)
class SafetyCheckResponse(BaseModel):
    passed : bool
    score : int = Field(...,ge=0,le=100)
    issues: List[str]