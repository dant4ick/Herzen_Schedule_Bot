import json
import logging
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from pathlib import Path
from data.config import BASE_DIR, ADMIN_TELEGRAM_ID
from scripts import keyboards
from scripts.bot import db, dp, bot

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
    with open(Path(BASE_DIR / 'data/groups.json'), 'r', encoding='UTF-8') as groups_json:
        groups = json.load(groups_json)
    return groups


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


async def generate_schedule_message(schedule):
    msg_text = ''
    for day in schedule:
        msg_text += f"\n🗓{day}\n"
        for course in schedule[day]:
            time = course['time']
            mod = course['mod']
            if mod:
                mod = "ℹ " + mod
            name = course['name']
            type = course['type']
            teacher = course['teacher']
            room = course['room']

            msg_text += f"\n⏰ {time} <i>{mod}</i>" \
                        f"\n<b>{name}</b> {type}"
            if teacher:
                msg_text += f"\n{teacher.strip()}"
            if room:
                msg_text += f"\n{room.strip()}"
            msg_text += "\n"
        msg_text += "\n"
    return msg_text


def extract_group_numbers(data):
    group_numbers = []

    if isinstance(data, dict):
        for key, value in data.items():
            group_numbers.extend(extract_group_numbers(value))
    elif isinstance(data, str):
        try:
            int(data)
            group_numbers.append(data)
        except ValueError:
            pass

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
    moscow_tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz=moscow_tz)
    wait_for = time.fromisoformat(wait_before)

    now_delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
    wait_for_delta = timedelta(hours=wait_for.hour, minutes=wait_for.minute, seconds=wait_for.second)
    pause = (wait_for_delta - now_delta).seconds
    return pause


async def notify_admins(message: str):
    msg_text = f"📢 <b>Внимание!</b>\n\n{message}"
    
    await bot.send_message(ADMIN_TELEGRAM_ID, msg_text, parse_mode='HTML')