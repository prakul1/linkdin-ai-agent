"""Schedule endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.schedule import ScheduleStatus
from app.schemas.schedule import (
    ScheduleCreateRequest, ScheduleResponse,
    SuggestTimesRequest, SuggestTimesResponse, SuggestedTime,
    ActiveJob,
)
from app.services.scheduler_service import SchedulerService
from app.api.deps import get_current_user
from app.utils.time_suggestions import suggest_posting_times
router = APIRouter(prefix="/api/schedules", tags=["schedules"])
def get_scheduler(db: Session = Depends(get_db)):
    return SchedulerService(db=db)
@router.post("", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    payload: ScheduleCreateRequest,
    user: User = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    return scheduler.schedule_post(
        post_id=payload.post_id, user_id=user.id, scheduled_at=payload.scheduled_at,
    )
@router.get("", response_model=List[ScheduleResponse])
def list_schedules(
    status_filter: Optional[ScheduleStatus] = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    return scheduler.list_schedules(user_id=user.id, status_filter=status_filter)
@router.get("/active-jobs", response_model=List[ActiveJob])
def list_active_jobs(scheduler: SchedulerService = Depends(get_scheduler)):
    return scheduler.list_active_jobs()
@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: int,
    user: User = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    return scheduler.get_schedule(schedule_id=schedule_id, user_id=user.id)
@router.post("/{schedule_id}/cancel", response_model=ScheduleResponse)
def cancel_schedule(
    schedule_id: int,
    user: User = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler),
):
    return scheduler.cancel_schedule(schedule_id=schedule_id, user_id=user.id)
@router.post("/suggest-times", response_model=SuggestTimesResponse)
def suggest_times(
    payload: SuggestTimesRequest,
    user: User = Depends(get_current_user),
):
    times = suggest_posting_times(count=payload.count, timezone_name=payload.timezone)
    return SuggestTimesResponse(
        timezone=payload.timezone,
        suggestions=[SuggestedTime(suggested_at=t) for t in times],
    )