"""Post service — now indexes approved posts into RAG."""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status as http_status
from app.models.post import Post, PostStatus, PostStyle
from app.schemas.post import PostGenerateRequest, PostUpdateRequest
from app.services.rag_service import RAGService
from app.utils.logger import logger
class PostService:
    def __init__(self, db: Session):
        self.db = db
    def generate_draft(self, user_id, payload):
        logger.info(f"Generating draft for user={user_id}, style={payload.style}")
        stub_content = self._generate_stub_content(payload)
        post = Post(
            user_id=user_id,
            topic=payload.topic,
            style=payload.style,
            content=stub_content,
            status=PostStatus.DRAFT,
            model_used="stub-v1",
            generation_attempts=1,
            safety_score=100,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post
    def _generate_stub_content(self, payload):
        style_intros = {
            PostStyle.FORMAL: "I am pleased to share that",
            PostStyle.STORYTELLING: "Let me tell you a story.",
            PostStyle.THOUGHT_LEADERSHIP: "Here's a thought worth sharing:",
        }
        intro = style_intros.get(payload.style, "")
        return f"[STUB - Phase 4 placeholder]\n\n{intro}\n\n{payload.topic}\n\n#LinkedIn #AI #Automation"
    def get_post(self, post_id, user_id):
        post = self.db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
        if not post:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
        return post
    def list_posts(self, user_id, offset, limit, status_filter=None, style_filter=None):
        query = self.db.query(Post).filter(Post.user_id == user_id)
        if status_filter:
            query = query.filter(Post.status == status_filter)
        if style_filter:
            query = query.filter(Post.style == style_filter)
        total = query.count()
        items = query.order_by(desc(Post.created_at)).offset(offset).limit(limit).all()
        return items, total
    def update_post(self, post_id, user_id, payload):
        post = self.get_post(post_id, user_id)
        if post.status not in (PostStatus.DRAFT, PostStatus.APPROVED):
            raise HTTPException(status_code=400, detail=f"Cannot edit post in status '{post.status}'")
        if payload.content is not None:
            post.content = payload.content
            post.user_edited = True
        if payload.hashtags is not None:
            post.hashtags = payload.hashtags
        self.db.commit()
        self.db.refresh(post)
        return post
    def approve_post(self, post_id, user_id):
        post = self.get_post(post_id, user_id)
        if post.status != PostStatus.DRAFT:
            raise HTTPException(status_code=400, detail=f"Only DRAFT can be approved. Current: {post.status}")
        post.status = PostStatus.APPROVED
        self.db.commit()
        self.db.refresh(post)
        logger.info(f"Post {post_id} APPROVED")
        # NEW: Index into RAG memory
        try:
            rag = RAGService(db=self.db)
            rag.upsert_post(
                post_id=post.id,
                user_id=post.user_id,
                content=post.content or "",
                topic=post.topic,
                style=post.style.value,
            )
        except Exception as e:
            logger.error(f"RAG indexing failed for post {post.id}: {e}")
        return post
    def reject_post(self, post_id, user_id, reason=None):
        post = self.get_post(post_id, user_id)
        if post.status != PostStatus.DRAFT:
            raise HTTPException(status_code=400, detail=f"Only DRAFT can be rejected. Current: {post.status}")
        post.status = PostStatus.REJECTED
        post.rejection_reason = reason
        self.db.commit()
        self.db.refresh(post)
        return post
    def delete_post(self, post_id, user_id):
        post = self.get_post(post_id, user_id)
        if post.status == PostStatus.PUBLISHED:
            raise HTTPException(status_code=400, detail="Cannot delete a published post")
        # NEW: Remove from vector store too
        try:
            rag = RAGService(db=self.db)
            rag.delete_post(post_id=post.id)
        except Exception as e:
            logger.error(f"RAG delete failed: {e}")
        self.db.delete(post)
        self.db.commit()