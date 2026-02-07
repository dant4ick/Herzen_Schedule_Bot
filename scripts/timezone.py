import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from data.config import TIMEZONE

_DEFAULT_TIMEZONE = "Europe/Moscow"
FACULTY_TIMEZONE_OVERRIDES: dict[int, str] = {
    122: "Asia/Tashkent",
}


def _resolve_timezone(name: str) -> tuple[str, ZoneInfo]:
    tz_name = name or _DEFAULT_TIMEZONE
    try:
        return tz_name, ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        if tz_name != _DEFAULT_TIMEZONE:
            logging.warning(
                "Timezone %s is not available. Falling back to %s.",
                tz_name,
                _DEFAULT_TIMEZONE,
            )
        return _DEFAULT_TIMEZONE, ZoneInfo(_DEFAULT_TIMEZONE)


TIMEZONE_NAME, TZINFO = _resolve_timezone(TIMEZONE)
FACULTY_TZINFO_OVERRIDES: dict[int, ZoneInfo] = {}
for faculty_id, tz_name in FACULTY_TIMEZONE_OVERRIDES.items():
    _, FACULTY_TZINFO_OVERRIDES[faculty_id] = _resolve_timezone(tz_name)


def tzinfo_for_faculty(faculty_id: int | None) -> ZoneInfo:
    if faculty_id is None:
        return TZINFO
    try:
        normalized_faculty_id = int(faculty_id)
    except (TypeError, ValueError):
        return TZINFO
    return FACULTY_TZINFO_OVERRIDES.get(normalized_faculty_id, TZINFO)


def tz_now() -> datetime:
    return datetime.now(tz=TZINFO)


def tz_today() -> date:
    return tz_now().date()
