"""Publisher service — Phase 8 stub. Phase 9 wires real LinkedIn."""
import uuid
from sqlalchemy.orm import Session
from app.models.post import Post
from app.utils.logger import logger
class PublisherService:
    def __init__(self, db: Session):
        self.db = db
    def publish(self, post: Post, user_id: int) -> str:
        logger.info(f"[PUBLISHER] Publishing post {post.id} for user {user_id}")
        return self._publish_to_linkedin(post, user_id)
    def _publish_to_linkedin(self, post: Post, user_id: int) -> str:
        logger.info("=" * 60)
        logger.info("SIMULATED LINKEDIN POST")
        logger.info("=" * 60)
        logger.info(f"User: {user_id}")
        logger.info(f"Topic: {post.topic}")
        logger.info(f"Content:\n{post.content}")
        logger.info(f"Hashtags: {post.hashtags}")
        logger.info("=" * 60)
        fake_id = f"urn:li:share:STUB-{uuid.uuid4().hex[:16]}"
        return fake_id