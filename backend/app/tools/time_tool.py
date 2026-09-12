from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field


class TimeInput(BaseModel):
    timezone: str = Field(default="UTC", min_length=1, max_length=64)


class TimeToolError(ValueError):
    """Raised when a requested timezone is invalid."""


def current_time(payload: TimeInput) -> dict[str, str]:
    try:
        zone = ZoneInfo(payload.timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise TimeToolError("不支持的时区") from exc
    now = datetime.now(timezone.utc).astimezone(zone)
    return {
        "timezone": payload.timezone,
        "iso": now.isoformat(),
        "formatted": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }
