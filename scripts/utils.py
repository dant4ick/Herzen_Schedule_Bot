import asyncio
import json
import logging
import random

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, Message
from aiogram.utils import exceptions
from aiogram.utils.callback_data import CallbackData

from pathlib import Path
from config import BASE_DIR
from scripts.handlers import keyboards
from scripts.bot import db

cb_data = CallbackData('data', 'num')


async def open_groups_file():
    with open(Path(BASE_DIR / 'groups.json'), 'r', encoding='UTF-8') as groups_json:
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
            if ' ' in mod:
                mod = mod.split(' ', maxsplit=1)
                if mod[0].strip('(),') == mod[1].strip('(),'):  # sometimes something like (8.09—6.10, 8.09—6.10) occurs
                    continue
                mod = "ℹ " + mod[1][0:-1]
                if '*' in mod:
                    mod = mod.split('*')[0]
            else:
                mod = ''

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
    return msg_text


async def validate_user(msg):
    user_data = db.get_user(msg.from_user.id)
    if not user_data:
        await msg.answer("Кажется, я не знаю, где ты учишься. "
                         "Пройди опрос, чтобы я мог вывести твое расписание.",
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(keyboards.bt_group_config))
        return False
    return True


async def get_random_chill_sticker():
    stickers = [
        'CAACAgIAAxkBAAEXjKZjC-Ky4494QMqmyAKgvTFV4fsJdQACoAwAAnUY2Et2hyIlXw_lYSkE',  # Blue cat party
        'CAACAgIAAxkBAAEXpeFjD6_B6sT32S6khtedymBXcFiVjgAC3goAAjHH2EuOfaJNnbW_JykE',  # Blue cat chill
        'CAACAgIAAxkBAAEXpd1jD6-6pRbe-UgQ2C_2vNtccmNnbwACzRMAAl6zyEvD5PzG428z7ykE',  # Real cat vibing
        'CAACAgIAAxkBAAEXpdtjD6-dRMqPJRtw405KJlvIcFiPVwACRBQAAgyeKEjz0Nb_G-GZ4SkE',  # Emoji party
        'CAACAgIAAxkBAAEXpd9jD6-9IxLBW0nmsjZ3_EYm8Q9dSgACIhQAAraw0EtoiZUwd4T4UykE',  # Pear party
        'CAACAgIAAxkBAAEXpeNjD6_GQ3TKcVOe0oKVNJoygASHXwACbQEAAiI3jgQl87gUwpqm8ikE'  # Kolobok party
    ]
    return stickers[random.randint(0, len(stickers) - 1)]


async def broadcast_message(user_id: int, message: Message):
    try:
        await message.forward(user_id, disable_notification=True)

    except exceptions.BotBlocked:
        logging.error(f"target id:{user_id} - blocked by user")
    except exceptions.ChatNotFound:
        logging.error(f"target id:{user_id} - chat not found")
    except exceptions.RetryAfter as e:
        logging.error(f"target id:{user_id} - flood limit, sleep {e.timeout} seconds")
        await asyncio.sleep(e.timeout)
        return await broadcast_message(user_id, message)
    except exceptions.UserDeactivated:
        logging.error(f"target id:{user_id} - user is deactivated")
    except exceptions.TelegramAPIError:
        logging.exception(f"target id:{user_id} - failed")
    else:
        logging.info(f"target id:{user_id}]: success")
        return True
    return False
