"""
One-off script: re-embed all approved/published posts into ChromaDB.
Run inside container:
  docker compose exec api python -m scripts.reindex_posts
"""
from app.db.session import SessionLocal
from app.models.post import Post, PostStatus
from app.services.rag_service import RAGService
from app.utils.logger import logger
def reindex_all():
    db = SessionLocal()
    try:
        posts = (
            db.query(Post)
            .filter(Post.status.in_([PostStatus.APPROVED, PostStatus.PUBLISHED]))
            .all()
        )
        logger.info(f"Found {len(posts)} posts to reindex")
        if not posts:
            return
        rag = RAGService(db=db)
        for post in posts:
            if not post.content:
                continue
            rag.upsert_post(
                post_id=post.id,
                user_id=post.user_id,
                content=post.content,
                topic=post.topic,
                style=post.style.value,
            )
        logger.info(f"Reindexed {len(posts)} posts")
    finally:
        db.close()
if __name__ == "__main__":
    reindex_all()