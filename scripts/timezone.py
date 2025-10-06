import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from data.config import TIMEZONE

_DEFAULT_TIMEZONE = "Europe/Moscow"


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


def tz_now() -> datetime:
    return datetime.now(tz=TZINFO)


def tz_today() -> date:
    return tz_now().date()
