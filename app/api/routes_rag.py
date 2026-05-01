"""RAG inspection / debug endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.rag_service import RAGService
from app.schemas.rag import (
    RetrieveRequest, RetrieveResponse, SimilarPostItem,
    RepetitionCheckRequest, RepetitionCheckResponse, RAGStatsResponse,
)
router = APIRouter(prefix="/api/rag", tags=["rag"])
@router.get("/stats", response_model=RAGStatsResponse)
def rag_stats(db: Session = Depends(get_db)):
    rag = RAGService(db=db)
    return rag.stats()
@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(
    payload: RetrieveRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rag = RAGService(db=db)
    results = rag.retrieve_similar(
        query_text=payload.query,
        user_id=user.id,
        top_k=payload.top_k,
        style_filter=payload.style_filter,
    )
    return RetrieveResponse(
        query=payload.query,
        results=[SimilarPostItem(**r) for r in results],
    )
@router.post("/check-repetition", response_model=RepetitionCheckResponse)
def check_repetition(
    payload: RepetitionCheckRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rag = RAGService(db=db)
    result = rag.check_repetition(
        new_content=payload.content,
        user_id=user.id,
        threshold=payload.threshold,
    )
    return RepetitionCheckResponse(**result)