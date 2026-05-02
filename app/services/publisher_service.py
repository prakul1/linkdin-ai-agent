"""Publisher service — Phase 9: Real LinkedIn + manual fallback."""
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.post import Post
from app.models.user import User
from app.services.linkedin_service import LinkedInService, LinkedInError
from app.utils.logger import logger
MANUAL_URN_PREFIX = "manual:"
class PublisherService:
    def __init__(self, db: Session):
        self.db = db
    def publish(self, post: Post, user_id: int) -> str:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise RuntimeError(f"User {user_id} not found")
        linkedin = LinkedInService(db=self.db)
        if linkedin.is_configured() and linkedin.is_user_connected(user):
            return self._publish_via_api(post, user, linkedin)
        else:
            return self._mark_for_manual_posting(post, user)
    def _publish_via_api(self, post, user, linkedin):
        logger.info(f"[PUBLISHER] AUTO mode for post {post.id} (user {user.id})")
        text = self._build_post_text(post)
        try:
            urn = linkedin.publish_text_post(
                access_token=user.linkedin_access_token,
                author_urn=user.linkedin_user_urn,
                text=text,
            )
            return urn
        except LinkedInError as e:
            logger.error(f"[PUBLISHER] LinkedIn API error: {e}")
            raise
    def _mark_for_manual_posting(self, post, user):
        logger.info(
            f"[PUBLISHER] MANUAL mode for post {post.id}: "
            f"User {user.id} hasn't connected LinkedIn."
        )
        logger.info("=" * 60)
        logger.info("MANUAL POST READY (user must copy/paste)")
        logger.info("=" * 60)
        logger.info(f"User: {user.id}")
        logger.info(f"Topic: {post.topic}")
        logger.info(f"Content:\n{self._build_post_text(post)}")
        logger.info("=" * 60)
        return f"{MANUAL_URN_PREFIX}{uuid.uuid4().hex[:16]}"
    @staticmethod
    def _build_post_text(post):
        text = (post.content or "").strip()
        if post.hashtags and post.hashtags not in text:
            text = f"{text}\n\n{post.hashtags}"
        return text
    @staticmethod
    def is_manual_urn(urn):
        return urn.startswith(MANUAL_URN_PREFIX) if urn else False