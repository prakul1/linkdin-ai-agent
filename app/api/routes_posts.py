"""Post CRUD endpoints."""
import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.models.post import PostStatus, PostStyle
from app.models.user import User
from app.schemas.post import (
    PostGenerateRequest,
    PostUpdateRequest,
    PostResponse,
    PostListItem,
)
from app.schemas.common import PaginatedResponse
from app.services.post_service import PostService
from app.api.deps import get_current_user, get_post_service
router = APIRouter(prefix="/api/posts", tags=["posts"])
@router.post("/generate", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def generate_post(
    payload: PostGenerateRequest,
    user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    return service.generate_draft(user_id=user.id, payload=payload)
@router.get("", response_model=PaginatedResponse[PostListItem])
def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[PostStatus] = Query(None, alias="status"),
    style_filter: Optional[PostStyle] = Query(None, alias="style"),
    user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    offset = (page - 1) * page_size
    items, total = service.list_posts(
        user_id=user.id,
        offset=offset,
        limit=page_size,
        status_filter=status_filter,
        style_filter=style_filter,
    )
    return PaginatedResponse[PostListItem](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )
@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    return service.get_post(post_id=post_id, user_id=user.id)
@router.patch("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    payload: PostUpdateRequest,
    user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    return service.update_post(post_id=post_id, user_id=user.id, payload=payload)
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    service.delete_post(post_id=post_id, user_id=user.id)
    return None