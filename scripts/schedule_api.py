import datetime
import json
import logging
from typing import Any, Iterable

import requests as request
from redis import Redis

from data.config import REDIS_URL

API_BASE_URL = 'https://api.herzen.spb.ru/schedule/v1'

SCHEDULE_URL = f'{API_BASE_URL}/schedule'
GROUPS_URL = f'{API_BASE_URL}/groups'
SUB_GROUPS_URL = f'{API_BASE_URL}/sub_groups'
TEACHERS_URL = f'{API_BASE_URL}/teachers'
FACULTIES_URL = f'{API_BASE_URL}/faculties'
ROOMS_URL = f'{API_BASE_URL}/rooms'
BUILDINGS_URL = f'{API_BASE_URL}/buildings'

REQUEST_TIMEOUT = 10

GROUPS_CACHE_TTL = datetime.timedelta(hours=24)
REFERENCE_CACHE_TTL = datetime.timedelta(days=7)
SCHEDULE_CACHE_TTL = datetime.timedelta(hours=1)

GROUPS_CACHE_KEY = "groups:tree"
TEACHER_CACHE_PREFIX = "teacher"
ROOM_CACHE_PREFIX = "room"
BUILDING_CACHE_PREFIX = "building"

_redis_client: Redis | None = None
_redis_disabled = False


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _get_redis() -> Redis | None:
    global _redis_client, _redis_disabled
    if _redis_disabled:
        return None
    if _redis_client is not None:
        return _redis_client
    if not REDIS_URL:
        _redis_disabled = True
        return None
    try:
        client = Redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception as exc:
        logging.warning("Redis is unavailable: %s", exc)
        _redis_disabled = True
        return None

def request_json(url: str, params: dict | None = None, context: str = "request") -> Any | None:
    try:
        response = request.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except request.exceptions.Timeout:
        logging.error("Timeout error occurred during %s: %s", context, url)
        return None
    except request.exceptions.RequestException as exc:
        logging.error("Request error occurred during %s: %s (%s)", context, url, exc)
        return None

    if not response.ok:
        logging.error("API response error during %s: %s (%s)", context, response.url, response.status_code)
        return None

    try:
        return response.json()
    except ValueError:
        logging.error("Failed to decode JSON during %s: %s", context, response.url)
        return None


def _normalize_ids(values: Iterable[int]) -> list[int]:
    ids: list[int] = []
    for value in values:
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return sorted(set(ids))


def _cache_get_json(key: str) -> Any | None:
    redis_client = _get_redis()
    if not redis_client:
        return None
    try:
        cached = redis_client.get(key)
        if not cached:
            return None
        return json.loads(cached)
    except Exception as exc:
        logging.warning("Failed to read cache %s: %s", key, exc)
        return None


def _cache_set_json(key: str, value: Any, ttl: datetime.timedelta) -> None:
    redis_client = _get_redis()
    if not redis_client:
        return
    try:
        redis_client.setex(key, int(ttl.total_seconds()), json.dumps(value, ensure_ascii=False))
    except Exception as exc:
        logging.warning("Failed to write cache %s: %s", key, exc)


def _cache_get_many(prefix: str, ids: list[int]) -> tuple[dict[int, dict[str, Any]], list[int]]:
    redis_client = _get_redis()
    if not redis_client:
        return {}, ids
    keys = [f"{prefix}:{item_id}" for item_id in ids]
    try:
        values = redis_client.mget(keys)
    except Exception as exc:
        logging.warning("Failed to read cache %s: %s", prefix, exc)
        return {}, ids

    found: dict[int, dict[str, Any]] = {}
    missing: list[int] = []
    for item_id, raw in zip(ids, values):
        if raw:
            try:
                found[item_id] = json.loads(raw)
            except Exception:
                missing.append(item_id)
        else:
            missing.append(item_id)
    return found, missing


def _cache_set_many(prefix: str, items: Iterable[dict[str, Any]], ttl: datetime.timedelta) -> None:
    redis_client = _get_redis()
    if not redis_client:
        return
    ttl_seconds = int(ttl.total_seconds())
    try:
        pipeline = redis_client.pipeline()
        for item in items:
            raw_id = item.get("id")
            if raw_id is None:
                continue
            try:
                item_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            key = f"{prefix}:{item_id}"
            pipeline.setex(key, ttl_seconds, json.dumps(item, ensure_ascii=False))
        pipeline.execute()
    except Exception as exc:
        logging.warning("Failed to write cache %s: %s", prefix, exc)

def _schedule_cache_key(group_id: int, start_date: datetime.date, end_date: datetime.date,
                        sub_group_id: int | None = None, exam_only: bool | None = None) -> str:
    sub_value = sub_group_id if sub_group_id is not None else 0
    exam_value = 1 if exam_only else 0
    return f"schedule:{group_id}:{sub_value}:{start_date.isoformat()}:{end_date.isoformat()}:{exam_value}"


def _build_groups_tree(groups_data: list[dict[str, Any]], faculties_data: list[dict[str, Any]],
                       sub_groups_data: list[dict[str, Any]]) -> dict[str, Any]:
    faculties_map = {}
    for item in faculties_data:
        raw_id = item.get("id")
        if raw_id is None:
            continue
        try:
            faculty_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        faculties_map[faculty_id] = item.get("name", "")

    sub_group_details: dict[int, dict[str, Any]] = {}
    for sub_group in sub_groups_data:
        try:
            sub_group_id = int(sub_group.get("id"))
        except (TypeError, ValueError):
            continue
        sub_group_details[sub_group_id] = sub_group

    groups_tree: dict[str, dict[str, dict[str, dict[str, dict[str, dict[str, Any]]]]]] = {}

    def sort_key(item: dict[str, Any]) -> tuple:
        faculty_name = faculties_map.get(item.get("faculty_id"), f"Факультет {item.get('faculty_id')}")
        return (
            faculty_name,
            item.get("education_form") or "",
            item.get("education_level") or "",
            item.get("course") or 0,
            item.get("name") or "",
        )

    for group in sorted(groups_data, key=sort_key):
        try:
            group_id = int(group.get("id"))
        except (TypeError, ValueError):
            continue

        faculty_name = faculties_map.get(group.get("faculty_id"), f"Факультет {group.get('faculty_id')}")
        form = group.get("education_form") or "неизвестно"
        level = group.get("education_level") or "неизвестно"
        course = str(group.get("course") or "")
        group_name = group.get("name") or f"Группа {group_id}"

        leaf: dict[str, Any] = {"id": group_id}
        sub_group_ids = group.get("sub_group_ids") or []
        if isinstance(sub_group_ids, list) and sub_group_ids:
            sub_groups = []
            for sub_group_id in sub_group_ids:
                try:
                    sub_group_id = int(sub_group_id)
                except (TypeError, ValueError):
                    continue
                detail = sub_group_details.get(sub_group_id, {})
                sub_groups.append({
                    "id": sub_group_id,
                    "name": detail.get("name") or str(len(sub_groups) + 1),
                })
            if sub_groups:
                leaf["sub_groups"] = sub_groups

        faculty_bucket = groups_tree.setdefault(faculty_name, {})
        form_bucket = faculty_bucket.setdefault(form, {})
        level_bucket = form_bucket.setdefault(level, {})
        course_bucket = level_bucket.setdefault(course, {})
        course_bucket[group_name] = leaf

    return groups_tree


def _fetch_groups_tree() -> dict[str, Any] | None:
    groups_data = request_json(GROUPS_URL, context="groups")
    faculties_data = request_json(FACULTIES_URL, context="faculties")
    sub_groups_data = request_json(SUB_GROUPS_URL, context="sub_groups")

    if not isinstance(groups_data, list) or not isinstance(faculties_data, list) or not isinstance(sub_groups_data, list):
        return None

    groups_tree = _build_groups_tree(groups_data, faculties_data, sub_groups_data)
    if not groups_tree:
        return None
    return groups_tree


def get_groups_tree(force_refresh: bool = False) -> dict[str, Any] | None:
    if not force_refresh:
        cached_data = _cache_get_json(GROUPS_CACHE_KEY)
        if cached_data:
            return cached_data

    groups_tree = _fetch_groups_tree()
    if groups_tree:
        _cache_set_json(GROUPS_CACHE_KEY, groups_tree, GROUPS_CACHE_TTL)
        return groups_tree
    return None


def refresh_groups_cache() -> bool:
    groups_tree = _fetch_groups_tree()
    if not groups_tree:
        return False
    _cache_set_json(GROUPS_CACHE_KEY, groups_tree, GROUPS_CACHE_TTL)
    return True


def get_schedule(group_id: int, start_date: datetime.date, end_date: datetime.date,
                 sub_group_id: int | None = None, exam_only: bool | None = None) -> Any | None:
    params = {
        "group_id": group_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    if sub_group_id not in (None, 0, "0"):
        params["sub_group_id"] = sub_group_id
    if exam_only is not None:
        params["exam_only"] = exam_only

    redis_client = _get_redis()
    cache_key = _schedule_cache_key(group_id, start_date, end_date, sub_group_id, exam_only)

    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as exc:
            logging.warning("Failed to read schedule cache: %s", exc)

    data = request_json(SCHEDULE_URL, params=params, context="schedule")
    if data is None:
        return None

    if redis_client and isinstance(data, list):
        try:
            redis_client.setex(cache_key, int(SCHEDULE_CACHE_TTL.total_seconds()),
                               json.dumps(data, ensure_ascii=False))
        except Exception as exc:
            logging.warning("Failed to write schedule cache: %s", exc)

    return data


def get_teachers(teacher_ids: Iterable[int]) -> dict[int, dict[str, Any]]:
    ids = _normalize_ids(teacher_ids)
    if not ids:
        return {}

    found, missing = _cache_get_many(TEACHER_CACHE_PREFIX, ids)

    if missing:
        data = request_json(TEACHERS_URL, params={"teacher_ids": ",".join(map(str, missing))}, context="teachers")
        if isinstance(data, list):
            _cache_set_many(TEACHER_CACHE_PREFIX, data, REFERENCE_CACHE_TTL)
            for item in data:
                raw_id = item.get("id")
                if raw_id is None:
                    continue
                try:
                    found[int(raw_id)] = item
                except (TypeError, ValueError):
                    continue

    return found


def get_rooms(room_ids: Iterable[int]) -> dict[int, dict[str, Any]]:
    ids = _normalize_ids(room_ids)
    if not ids:
        return {}

    found, missing = _cache_get_many(ROOM_CACHE_PREFIX, ids)

    if missing:
        data = request_json(ROOMS_URL, params={"room_ids": ",".join(map(str, missing))}, context="rooms")
        if isinstance(data, list):
            _cache_set_many(ROOM_CACHE_PREFIX, data, REFERENCE_CACHE_TTL)
            for item in data:
                raw_id = item.get("id")
                if raw_id is None:
                    continue
                try:
                    found[int(raw_id)] = item
                except (TypeError, ValueError):
                    continue

    return found


def get_buildings(building_ids: Iterable[int]) -> dict[int, dict[str, Any]]:
    ids = _normalize_ids(building_ids)
    if not ids:
        return {}

    found, missing = _cache_get_many(BUILDING_CACHE_PREFIX, ids)

    if missing:
        data = request_json(BUILDINGS_URL, params={"building_ids": ",".join(map(str, missing))}, context="buildings")
        if isinstance(data, list):
            _cache_set_many(BUILDING_CACHE_PREFIX, data, REFERENCE_CACHE_TTL)
            for item in data:
                raw_id = item.get("id")
                if raw_id is None:
                    continue
                try:
                    found[int(raw_id)] = item
                except (TypeError, ValueError):
                    continue

    return found
