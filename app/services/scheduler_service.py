"""Scheduler service — APScheduler with SQLAlchemy persistence."""
from datetime import datetime, timezone
from typing import List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.config import settings
from app.models.post import Post, PostStatus
from app.models.schedule import Schedule, ScheduleStatus
from app.jobs.publish_job import publish_post_job
from app.utils.logger import logger
def _job_id_for_schedule(schedule_id: int) -> str:
    return f"publish_schedule_{schedule_id}"
class SchedulerService:
    _scheduler: Optional[BackgroundScheduler] = None
    @classmethod
    def start(cls) -> None:
        if cls._scheduler is not None and cls._scheduler.running:
            return
        jobstore = SQLAlchemyJobStore(url=settings.database_url)
        cls._scheduler = BackgroundScheduler(
            jobstores={"default": jobstore},
            executors={"default": ThreadPoolExecutor(max_workers=4)},
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 3600,
            },
            timezone="UTC",
        )
        cls._scheduler.start()
        logger.info("[SCHEDULER] Started with SQLAlchemy job store")
    @classmethod
    def shutdown(cls) -> None:
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown(wait=False)
            logger.info("[SCHEDULER] Stopped")
    def __init__(self, db: Session):
        self.db = db
    @property
    def scheduler(self):
        if self.__class__._scheduler is None:
            raise RuntimeError("Scheduler not started")
        return self.__class__._scheduler
    def schedule_post(self, post_id, user_id, scheduled_at):
        post = self.db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
        if not post:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
        if post.status != PostStatus.APPROVED:
            raise HTTPException(status_code=400,
                detail=f"Only APPROVED posts can be scheduled. Current: {post.status}")
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if scheduled_at <= now:
            raise HTTPException(status_code=400, detail="scheduled_at must be in the future")
        schedule = Schedule(
            post_id=post.id, scheduled_at=scheduled_at,
            status=ScheduleStatus.PENDING, attempts=0, max_attempts=3,
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        job_id = _job_id_for_schedule(schedule.id)
        self.scheduler.add_job(
            func=publish_post_job, trigger="date", run_date=scheduled_at,
            args=[schedule.id], id=job_id,
            replace_existing=True, misfire_grace_time=3600,
        )
        post.status = PostStatus.SCHEDULED
        self.db.commit()
        logger.info(f"[SCHEDULER] Scheduled post {post.id} for {scheduled_at}")
        return schedule
    def cancel_schedule(self, schedule_id, user_id):
        schedule = (
            self.db.query(Schedule)
            .join(Post, Schedule.post_id == Post.id)
            .filter(Schedule.id == schedule_id, Post.user_id == user_id)
            .first()
        )
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        if schedule.status not in (ScheduleStatus.PENDING, ScheduleStatus.FAILED):
            raise HTTPException(status_code=400,
                detail=f"Cannot cancel schedule in status '{schedule.status}'")
        job_id = _job_id_for_schedule(schedule.id)
        try:
            self.scheduler.remove_job(job_id)
        except Exception as e:
            logger.warning(f"[SCHEDULER] Could not remove job {job_id}: {e}")
        schedule.status = ScheduleStatus.CANCELLED
        post = self.db.query(Post).filter(Post.id == schedule.post_id).first()
        if post and post.status == PostStatus.SCHEDULED:
            post.status = PostStatus.APPROVED
        self.db.commit()
        self.db.refresh(schedule)
        return schedule
    def list_schedules(self, user_id, status_filter=None):
        query = (
            self.db.query(Schedule)
            .join(Post, Schedule.post_id == Post.id)
            .filter(Post.user_id == user_id)
        )
        if status_filter:
            query = query.filter(Schedule.status == status_filter)
        return query.order_by(Schedule.scheduled_at.desc()).all()
    def get_schedule(self, schedule_id, user_id):
        schedule = (
            self.db.query(Schedule)
            .join(Post, Schedule.post_id == Post.id)
            .filter(Schedule.id == schedule_id, Post.user_id == user_id)
            .first()
        )
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return schedule
    def list_active_jobs(self):
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": j.id,
                "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
                "args": j.args,
            }
            for j in jobs
        ]