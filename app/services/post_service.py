"""Post service — Phase 7: feeds attachment text into the agent."""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status as http_status
from app.config import settings
from app.models.post import Post, PostStatus, PostStyle
from app.models.attachment import Attachment
from app.schemas.post import PostGenerateRequest, PostUpdateRequest
from app.services.rag_service import RAGService
from app.services.storage_service import StorageService
from app.agent.graph import run_agent
from app.utils.logger import logger
class PostService:
    def __init__(self, db):
        self.db = db
    def generate_draft(self, user_id, payload):
        logger.info(f"Generating draft for user={user_id}, style={payload.style}")
        post = Post(
            user_id=user_id,
            topic=payload.topic,
            style=payload.style,
            content=None,
            status=PostStatus.DRAFT,
            model_used=settings.openai_model,
            generation_attempts=0,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        attachment_context = []
        if payload.attachment_ids:
            attachment_context = self._load_attachments(
                user_id=user_id,
                attachment_ids=payload.attachment_ids,
                target_post_id=post.id,
            )
        try:
            final_state = run_agent(
                db=self.db,
                user_id=user_id,
                post_id=post.id,
                topic=payload.topic,
                style=payload.style,
                additional_instructions=payload.additional_instructions,
                attachment_context=attachment_context,
            )
        except Exception as e:
            logger.error(f"Agent failed: {e}")
            post.status = PostStatus.FAILED
            self.db.commit()
            raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")
        post.content = final_state.get("final_content") or final_state.get("draft_content", "")
        post.hashtags = final_state.get("hashtags", "")
        post.safety_score = final_state.get("safety_score", 0)
        post.generation_attempts = final_state.get("generation_attempts", 1)
        self.db.commit()
        self.db.refresh(post)
        return post
    def _load_attachments(self, user_id, attachment_ids, target_post_id):
        atts = (
            self.db.query(Attachment)
            .join(Post, Attachment.post_id == Post.id)
            .filter(Attachment.id.in_(attachment_ids), Post.user_id == user_id)
            .all()
        )
        found_ids = {a.id for a in atts}
        missing = set(attachment_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Attachments not found: {sorted(missing)}",
            )
        context = []
        for a in atts:
            if a.post_id != target_post_id:
                a.post_id = target_post_id
            context.append({
                "type": a.file_type.value,
                "source": a.original_filename or a.url or "",
                "text": a.extracted_text or "",
            })
        self.db.commit()
        return context
    # ... (rest of methods: get_post, list_posts, update_post, approve_post,
    #      reject_post, delete_post — unchanged from Phase 6 except delete_post
    #      now also deletes attachment files via StorageService)
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
            raise HTTPException(status_code=400, detail=f"Only DRAFT can be approved")
        post.status = PostStatus.APPROVED
        self.db.commit()
        self.db.refresh(post)
        try:
            rag = RAGService(db=self.db)
            rag.upsert_post(
                post_id=post.id, user_id=post.user_id,
                content=post.content or "", topic=post.topic,
                style=post.style.value,
            )
        except Exception as e:
            logger.error(f"RAG indexing failed: {e}")
        return post
    def reject_post(self, post_id, user_id, reason=None):
        post = self.get_post(post_id, user_id)
        if post.status != PostStatus.DRAFT:
            raise HTTPException(status_code=400, detail=f"Only DRAFT can be rejected")
        post.status = PostStatus.REJECTED
        post.rejection_reason = reason
        self.db.commit()
        self.db.refresh(post)
        return post
    def delete_post(self, post_id, user_id):
        post = self.get_post(post_id, user_id)
        if post.status == PostStatus.PUBLISHED:
            raise HTTPException(status_code=400, detail="Cannot delete a published post")
        # Delete attachment files from disk
        storage = StorageService()
        for att in post.attachments:
            if att.file_path:
                storage.delete_file(att.file_path)
        try:
            rag = RAGService(db=self.db)
            rag.delete_post(post_id=post.id)
        except Exception as e:
            logger.error(f"RAG delete failed: {e}")
        self.db.delete(post)
        self.db.commit()