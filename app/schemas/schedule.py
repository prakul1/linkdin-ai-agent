"""Schedule-related schemas."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.models.schedule import ScheduleStatus
class ScheduleCreateRequest(BaseModel):
    post_id: int
    scheduled_at: datetime
class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    post_id: int
    scheduled_at: datetime
    status: ScheduleStatus
    attempts: int
    max_attempts: int
    posted_at: Optional[datetime] = None
    linkedin_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
class SuggestTimesRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)
    timezone: str = Field(default="UTC")
    @field_validator("timezone")
    @classmethod
    def validate_tz(cls, v):
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Unknown timezone: {v}")
        return v
class SuggestedTime(BaseModel):
    suggested_at: datetime
    reason: str = "High-engagement window for LinkedIn"
class SuggestTimesResponse(BaseModel):
    timezone: str
    suggestions: List[SuggestedTime]
class ActiveJob(BaseModel):
    id: str
    next_run_time: Optional[str]
    args: List