"""The job that runs when a scheduled time arrives."""
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.models.post import Post, PostStatus
from app.models.schedule import Schedule, ScheduleStatus
from app.services.publisher_service import PublisherService
from app.utils.logger import logger
def publish_post_job(schedule_id: int) -> None:
    logger.info(f"[JOB] publish_post_job triggered for schedule_id={schedule_id}")
    db = SessionLocal()
    try:
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            logger.error(f"[JOB] Schedule {schedule_id} not found")
            return
        if schedule.status in (ScheduleStatus.COMPLETED, ScheduleStatus.CANCELLED):
            logger.warning(f"[JOB] Schedule {schedule_id} already terminal — skipping")
            return
        post = db.query(Post).filter(Post.id == schedule.post_id).first()
        if not post:
            schedule.status = ScheduleStatus.FAILED
            schedule.error_message = "Post no longer exists"
            db.commit()
            return
        schedule.status = ScheduleStatus.RUNNING
        schedule.attempts += 1
        post.status = PostStatus.PUBLISHING
        db.commit()
        publisher = PublisherService(db=db)
        try:
            linkedin_post_id = publisher.publish(post=post, user_id=post.user_id)
        except Exception as e:
            logger.error(f"[JOB] Publish failed: {e}")
            _handle_failure(db, schedule, post, str(e))
            return
        schedule.status = ScheduleStatus.COMPLETED
        schedule.posted_at = datetime.now(timezone.utc)
        schedule.linkedin_post_id = linkedin_post_id
        post.status = PostStatus.PUBLISHED
        db.commit()
        logger.info(f"[JOB] Published post {post.id}. URN: {linkedin_post_id}")
    except Exception as e:
        logger.exception(f"[JOB] Unexpected error: {e}")
    finally:
        db.close()
def _handle_failure(db, schedule, post, error_msg):
    schedule.error_message = error_msg[:1000]
    if schedule.attempts < schedule.max_attempts:
        schedule.status = ScheduleStatus.FAILED
        post.status = PostStatus.FAILED
        logger.warning(f"[JOB] Failed (attempt {schedule.attempts}/{schedule.max_attempts})")
    else:
        schedule.status = ScheduleStatus.FAILED
        post.status = PostStatus.FAILED
        logger.error(f"[JOB] Permanently failed after {schedule.attempts} attempts")
    db.commit()