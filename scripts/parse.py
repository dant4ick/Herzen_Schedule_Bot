import asyncio
import datetime
import logging
from typing import Any

from scripts.timezone import TZINFO
from scripts.utils import seconds_before_iso_time
from scripts import schedule_api

WEEKDAYS_RU = [
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
]

def _parse_iso_datetime(value: str | None) -> datetime.datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        parsed = datetime.datetime.fromisoformat(value)
    except ValueError:
        logging.warning("Failed to parse datetime: %s", value)
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=TZINFO)
    return parsed


def _format_day_label(date_value: datetime.date) -> str:
    weekday = WEEKDAYS_RU[date_value.weekday()]
    day = str(date_value.day)
    month = f"{date_value.month:02d}"
    return f"{day}.{month}.{date_value.year}, {weekday}"


def _build_non_summer_ranges(start_date: datetime.date, end_date: datetime.date) -> list[tuple[datetime.date, datetime.date]]:
    summer_start = datetime.date(start_date.year, 6, 1)
    summer_end = datetime.date(start_date.year, 8, 31)

    if end_date < summer_start or start_date > summer_end:
        return [(start_date, end_date)]

    ranges: list[tuple[datetime.date, datetime.date]] = []
    if start_date < summer_start:
        ranges.append((start_date, min(end_date, summer_start - datetime.timedelta(days=1))))
    if end_date > summer_end:
        ranges.append((max(start_date, summer_end + datetime.timedelta(days=1)), end_date))

    return ranges


def parse_groups() -> None:
    if schedule_api.refresh_groups_cache():
        logging.info("updated groups successfully")
    else:
        logging.info("can't update groups list: api response is invalid")


def _build_schedule(items: list[dict[str, Any]], teachers: dict[int, dict[str, Any]],
                    rooms: dict[int, dict[str, Any]], buildings: dict[int, dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    schedule: dict[str, list[dict[str, str]]] = {}

    def format_rank(rank: str) -> str:
        rank = (rank or "").strip()
        if not rank:
            return ""
        if "." in rank:
            return rank
        lowered = rank.lower()
        if "старш" in lowered and "преп" in lowered:
            return "ст. преп."
        if "завед" in lowered and "каф" in lowered:
            return "зав. каф."
        if "проф" in lowered:
            return "проф."
        if "доцент" in lowered:
            return "доц."
        if "ассист" in lowered:
            return "асс."
        if "препод" in lowered:
            return "преп."
        return rank

    parsed_items = []
    for item in items:
        start_dt = _parse_iso_datetime(item.get("start_time"))
        end_dt = _parse_iso_datetime(item.get("end_time"))
        if not start_dt or not end_dt:
            continue

        parsed_items.append((start_dt.astimezone(TZINFO), end_dt.astimezone(TZINFO), item))

    for start_dt, end_dt, item in sorted(parsed_items, key=lambda entry: entry[0]):
        day_label = _format_day_label(start_dt.date())
        time_text = f"{start_dt:%H:%M} — {end_dt:%H:%M}"
        teacher_id = item.get("teacher_id")
        room_id = item.get("room_id")

        teacher_name = ""
        teacher_url = ""
        if teacher_id is not None:
            teacher_data = teachers.get(int(teacher_id), {})
            teacher_rank = format_rank(teacher_data.get("rank") or "")
            teacher_full_name = teacher_data.get("name") or ""
            teacher_url = teacher_data.get("atlas_url") or ""
            if teacher_rank and teacher_full_name:
                teacher_name = f"{teacher_rank} {teacher_full_name}".strip()
            else:
                teacher_name = teacher_full_name or teacher_rank

        room_name = ""
        if room_id is not None:
            room_data = rooms.get(int(room_id), {})
            room_name = room_data.get("name") or ""
            building_name = ""
            building_id = room_data.get("building_id")
            if building_id is not None:
                building_name = buildings.get(int(building_id), {}).get("name", "")
            if room_name and building_name:
                room_name = f"{room_name}, {building_name}"
            elif building_name:
                room_name = building_name

        schedule.setdefault(day_label, []).append({
            "time": time_text,
            "mod": item.get("note") or "",
            "name": item.get("name") or "",
            "type": item.get("type") or "",
            "teacher": teacher_name,
            "teacher_url": teacher_url,
            "room": room_name,
            "class_url": item.get("class_url") or "",
        })

    return schedule


async def parse_date_schedule(group, sub_group=None, date_1=None, date_2=None):
    if date_1 and not date_2:
        date_2 = date_1

    url = f"https://guide.herzen.spb.ru/schedule/{group}/by-dates"

    resolved_sub_group = None
    if sub_group not in (None, 0, "0"):
        try:
            sub_group_int = int(sub_group)
        except (TypeError, ValueError):
            sub_group_int = None

        if sub_group_int is not None:
            if sub_group_int in (1, 2):
                try:
                    group_int = int(group)
                    resolved_sub_group = int(f"{group_int}{sub_group_int}")
                except (TypeError, ValueError):
                    resolved_sub_group = sub_group_int
            else:
                resolved_sub_group = sub_group_int

    date_ranges = _build_non_summer_ranges(date_1, date_2)
    if not date_ranges:
        return {}, url

    schedule_items: list[dict[str, Any]] = []
    for start_date, end_date in date_ranges:
        schedule_response = schedule_api.get_schedule(group, start_date, end_date, sub_group_id=resolved_sub_group)
        if schedule_response is None:
            return None, url
        if not isinstance(schedule_response, list):
            logging.error("unexpected schedule response for group %s: %s", group, type(schedule_response))
            return None, url
        schedule_items.extend(schedule_response)

    if not schedule_items:
        return {}, url

    teacher_ids = {item.get("teacher_id") for item in schedule_items if item.get("teacher_id") is not None}
    room_ids = {item.get("room_id") for item in schedule_items if item.get("room_id") is not None}

    teachers = schedule_api.get_teachers(teacher_ids)
    rooms = schedule_api.get_rooms(room_ids)
    building_ids = {room.get("building_id") for room in rooms.values() if room.get("building_id") is not None}
    buildings = schedule_api.get_buildings(building_ids)

    schedule = _build_schedule(schedule_items, teachers, rooms, buildings)
    return schedule, url


async def update_groups(time_to_update: str = None):
    while True:
        logging.info("starting to update groups")
        parse_groups()

        if not time_to_update:
            break
        await asyncio.sleep(1)

        pause = await seconds_before_iso_time(time_to_update)
        await asyncio.sleep(pause)
