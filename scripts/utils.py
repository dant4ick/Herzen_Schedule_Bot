import json
import logging
from datetime import datetime, timedelta, time

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, Message
from aiogram.utils.callback_data import CallbackData

from pathlib import Path
from data.config import BASE_DIR
from scripts import keyboards
from scripts.bot import db, dp

cb_data = CallbackData('data', 'num')


async def open_groups_file():
    with open(Path(BASE_DIR / 'data/groups.json'), 'r', encoding='UTF-8') as groups_json:
        groups = json.load(groups_json)
    return groups


async def generate_kb_nums(source):
    msg_text = ''
    counter = 1
    inline_kb_numbers = InlineKeyboardMarkup(row_width=8)
    for data in source.keys():
        msg_text += f"{counter}. {data[0].upper() + data[1:]}\n"
        inline_kb_numbers.insert(InlineKeyboardButton(f'{counter}', callback_data=cb_data.new(num=counter)))
        counter += 1
    return msg_text, inline_kb_numbers


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


async def validate_user(user_id: int):
    user_data = db.get_user(user_id)
    if not user_data:
        await dp.bot.send_message(user_id, "Кажется, я не знаю, где ты учишься. "
                                           "Пройди опрос, чтобы я мог вывести твое расписание.",
                                  reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(keyboards.bt_group_config))
        return False
    return True


async def throttled(*args, **kwargs):
    msg = args[0]
    logging.info(f"throttled: {msg.from_user.id} (@{msg.from_user.username})")
    await msg.answer(f"Подожди {kwargs['rate']} сек. Я обязательно отвечу, но не так быстро.")


async def seconds_before_iso_time(wait_before: str):
    now = datetime.now()
    wait_for = time.fromisoformat(wait_before)

    now_delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
    wait_for_delta = timedelta(hours=wait_for.hour, minutes=wait_for.minute, seconds=wait_for.second)
    pause = (wait_for_delta - now_delta).seconds
    return pause
