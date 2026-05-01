"""Smart posting time suggestions based on LinkedIn engagement data."""
from datetime import datetime, timedelta, time
from typing import List
from zoneinfo import ZoneInfo
BEST_HOURS_BY_WEEKDAY = {
    0: [10, 12],
    1: [8, 9, 12, 17],
    2: [8, 9, 12, 17],
    3: [8, 9, 12, 17],
    4: [10, 12],
    5: [11],
    6: [11],
}
def suggest_posting_times(
    count: int = 5,
    timezone_name: str = "UTC",
    earliest_offset_minutes: int = 30,
) -> List[datetime]:
    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    earliest = now + timedelta(minutes=earliest_offset_minutes)
    suggestions: List[datetime] = []
    day_offset = 0
    max_days_to_search = 14
    while len(suggestions) < count and day_offset < max_days_to_search:
        candidate_date = (now + timedelta(days=day_offset)).date()
        weekday = candidate_date.weekday()
        hours = BEST_HOURS_BY_WEEKDAY.get(weekday, [])
        for hour in hours:
            candidate = datetime.combine(candidate_date, time(hour, 0), tzinfo=tz)
            if candidate >= earliest:
                suggestions.append(candidate)
                if len(suggestions) >= count:
                    break
        day_offset += 1
    return suggestions