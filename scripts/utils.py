import logging
from datetime import datetime, timedelta, time

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.config import ADMIN_TELEGRAM_ID
from scripts import keyboards
from scripts.bot import db, dp, bot
from scripts import schedule_api
from scripts.timezone import tz_now

day_pattern = r"(\b((0[1-9])|([1-2]\d)|(3[0-1])|([1-9])))"
month_pattern = r"(\.((0[1-9])|(1[0-2])|([1-9]))\b)"
year_pattern = r"(\.(\d{4}))"
date_pattern = r"({0}{1}({2})?)".format(day_pattern, month_pattern, year_pattern)
date_range_pattern = r"({0}\-{1})".format(date_pattern, date_pattern)

def get_dates_regexp() -> str:
    
    return r"((\A|\s|\b)({r}|{d})(\Z|\s))".format(r=date_range_pattern, d=date_pattern)


class NumCallback(CallbackData, prefix="data"):
    num: int


async def open_groups_file():
    groups = schedule_api.get_groups_tree()
    return groups or {}


def _resolve_sub_group_name(sub_groups, sub_group_id):
    if not sub_group_id:
        return None
    try:
        sub_group_id = int(sub_group_id)
    except (TypeError, ValueError):
        return None
    if sub_group_id == 0:
        return None
    for index, sub_group in enumerate(sub_groups, start=1):
        try:
            if int(sub_group.get("id")) == sub_group_id:
                return sub_group.get("name") or str(index)
        except (TypeError, ValueError):
            continue
    if 1 <= sub_group_id <= len(sub_groups):
        return sub_groups[sub_group_id - 1].get("name") or str(sub_group_id)
    return str(sub_group_id)


def find_group_info(groups, group_id, sub_group_id=None):
    try:
        target_id = int(group_id)
    except (TypeError, ValueError):
        return None, None

    for key, value in groups.items():
        if isinstance(value, dict):
            if "id" in value:
                try:
                    if int(value.get("id")) == target_id:
                        sub_groups = value.get("sub_groups") or []
                        return key, _resolve_sub_group_name(sub_groups, sub_group_id)
                except (TypeError, ValueError):
                    continue
            group_name, sub_group_name = find_group_info(value, target_id, sub_group_id)
            if group_name:
                return group_name, sub_group_name
        elif isinstance(value, (int, str)):
            try:
                if int(value) == target_id:
                    return key, None
            except (TypeError, ValueError):
                continue

    return None, None


async def generate_kb_nums(source):
    msg_text = ''
    counter = 1
    builder = InlineKeyboardBuilder()
    for data in source.keys():
        msg_text += f"{counter}. {data[0].upper() + data[1:]}\n"
        builder.button(text=f'{counter}', callback_data=NumCallback(num=counter).pack())
        counter += 1
    # builder.adjust(8)
    builder.row(keyboards.inline_bt_cancel)
    return msg_text, builder.as_markup()


def _format_course(course):
    time = course['time']
    mod = course['mod']
    if mod:
        mod = "ℹ " + mod
    name = course['name']
    type = course['type']
    teacher = course['teacher']
    room = course['room']
    class_url = course.get('class_url')
    teacher_url = course.get('teacher_url')

    type_label = (type or "").strip()
    if type_label:
        type_label = type_label.lower()
        type_label = {
            "лекция": "лекц",
            "практика": "практ",
            "лабораторная": "лаб",
            "семинар": "сем",
            "зачет": "зач",
            "зачёт": "зач",
            "экзамен": "экз",
            "консультация": "конс",
        }.get(type_label, type_label)

    title = name or ""
    if type_label:
        title = f"{title} [{type_label}]" if title else f"[{type_label}]"

    time_line = f"⏰ {time}"
    if mod:
        time_line += f" <i>{mod}</i>"

    if class_url:
        time_line += f" <a href=\"{class_url}\">🔗 (курс)</a>"

    lines = [f"\n{time_line}\n{title}"]
    if teacher:
        teacher_line = teacher.strip()
        if teacher_url:
            teacher_line = f"{teacher_line} <a href=\"{teacher_url}\">🔗 (профиль)</a>"
        lines.append(teacher_line)
    if room:
        lines.append(room.strip())
    lines.append("")
    return "\n".join(lines)


def _format_day(day: str, courses: list) -> str:
    """Format one day block (header + courses)."""
    block = f"\n🗓{day}\n"
    for course in courses:
        block += _format_course(course)
    return block + "\n"


async def generate_schedule_message(schedule):
    return "".join(_format_day(day, schedule[day]) for day in schedule)


async def generate_schedule_days(schedule) -> list:
    """Return list of day blocks (one string per day), for splitting long schedules by day."""
    return [_format_day(day, schedule[day]) for day in schedule]


def extract_group_numbers(data):
    group_numbers = []

    if isinstance(data, dict):
        if "id" in data and isinstance(data["id"], (int, str)):
            group_numbers.append(str(data["id"]))
            return group_numbers
        for value in data.values():
            group_numbers.extend(extract_group_numbers(value))
    elif isinstance(data, str):
        try:
            int(data)
            group_numbers.append(data)
        except ValueError:
            pass
    elif isinstance(data, int):
        group_numbers.append(str(data))

    return group_numbers


async def validate_user(user_id: int):
    user_data = db.get_user(user_id)

    groups_dict = await open_groups_file()
    groups_list = extract_group_numbers(groups_dict)

    if not user_data or str(user_data[0]) not in groups_list:
        await bot.send_message(user_id, f"Кажется, я не знаю, где ты учишься.\n"
                                        f"Нажми на кнопку <b>{keyboards.bt_group_config.text}</b>, чтобы я мог вывести твое расписание.",
                                  reply_markup=keyboards.kb_settings)
        return False
    return True


async def throttled(*args, **kwargs):
    msg = args[0]
    logging.info(f"throttled: {msg.from_user.id} (@{msg.from_user.username})")
    await msg.answer(f"Подожди {kwargs['rate']} сек. Я обязательно отвечу, но не так быстро.")


async def seconds_before_iso_time(wait_before: str):
    now = tz_now()
    wait_for = time.fromisoformat(wait_before)
    target = datetime.combine(now.date(), wait_for, tzinfo=now.tzinfo)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def notify_admins(message: str):
    msg_text = f"📢 <b>Внимание!</b>\n\n{message}"
    
    await bot.send_message(ADMIN_TELEGRAM_ID, msg_text, parse_mode='HTML')
