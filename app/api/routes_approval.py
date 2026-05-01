"""Approve / reject endpoints (human-in-the-loop)."""
from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.post import PostResponse, PostRejectRequest
from app.services.post_service import PostService
from app.api.deps import get_current_user, get_post_service
router = APIRouter(prefix="/api/posts", tags=["approval"])
@router.post("/{post_id}/approve", response_model=PostResponse)
def approve_post(
    post_id: int,
    user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    return service.approve_post(post_id=post_id, user_id=user.id)
@router.post("/{post_id}/reject", response_model=PostResponse)
def reject_post(
    post_id: int,
    payload: PostRejectRequest,
    user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    return service.reject_post(post_id=post_id, user_id=user.id, reason=payload.reason)