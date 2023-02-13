import asyncio
import json
import logging
import random
from datetime import datetime, timedelta, time

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, Message
from aiogram.utils import exceptions
from aiogram.utils.callback_data import CallbackData

from pathlib import Path
from data.config import BASE_DIR
from scripts import keyboards
from scripts.bot import db, dp
from scripts.parse import parse_date_schedule

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


async def send_date_schedule(user_id: int, schedule_response, period: str):
    logging.info(f"response: {schedule_response}")

    if schedule_response is None:
        await dp.bot.send_message(user_id, "😖 Упс, кажется, расписание не отвечает. Попробуй еще раз.")
        return

    if "недел" in period:
        if "эта" in period:
            period = "этой неделе"
        else:
            period = "следующей неделе"

    if not schedule_response:
        await dp.bot.send_message(user_id, f"🎉На {period} занятий нет, можно отдыхать.")
        await dp.bot.send_sticker(user_id, await get_random_chill_sticker())
        return

    schedule, url = schedule_response

    if "недел" in period:
        if "этой" in period:
            period = "эту неделю"
        else:
            period = "следующую неделю"

    msg_text = await generate_schedule_message(schedule)
    msg_len = len(msg_text)
    if msg_len > 4000:
        await dp.bot.send_message(user_id, "Сообщение получилось слишком длинным, "
                                           "так что придется смотреть по ссылке...",
                                  reply_markup=InlineKeyboardMarkup().add(
                                      InlineKeyboardButton('Проверить на сайте', f"{url}")
                                  ))
        return

    await dp.bot.send_message(user_id, f"Вот твое расписание на {period}:\n{msg_text}",
                              reply_markup=InlineKeyboardMarkup().add(
                                  InlineKeyboardButton('Проверить на сайте', f"{url}")
                              ))


async def mailing_schedule(mailing_time_str: str, schedule_date: str):
    while True:
        now = datetime.now()
        wait_for = time.fromisoformat(mailing_time_str)

        now_delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        wait_for_delta = timedelta(hours=wait_for.hour, minutes=wait_for.minute, seconds=wait_for.second)
        pause = (wait_for_delta - now_delta).seconds

        await asyncio.sleep(pause)
        logging.info(f"starting to mail schedules")
        mailing_list = db.get_mailing_list()
        for user_id, mailing_time in mailing_list:
            await broadcast_schedule(user_id, message_type=schedule_date)
            await asyncio.sleep(.1)
        await asyncio.sleep(1)


async def broadcast_schedule(user_id: int, message_type: str):
    try:
        if not await validate_user(user_id):
            logging.info(f"user validation failed during mailing - id: {user_id}")
            return
        group_id, sub_group = db.get_user(user_id)

        if message_type in "today":
            today = datetime.today().date()

            logging.info(f"attempted to mail today schedule - id: {user_id}")

            schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=today)
            await send_date_schedule(user_id, schedule_response, "сегодня")
        elif message_type in "tomorrow":
            tomorrow = datetime.today().date() + timedelta(days=1)

            logging.info(f"attempted to mail tomorrow schedule - id: {user_id}")

            schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=tomorrow)
            await send_date_schedule(user_id, schedule_response, "завтра")

    except exceptions.BotBlocked:
        logging.error(f"target id:{user_id} - blocked by user")
        db.del_user(user_id)
    except exceptions.ChatNotFound:
        db.del_user(user_id)
        logging.error(f"target id:{user_id} - chat not found")
    except exceptions.RetryAfter as e:
        logging.error(f"target id:{user_id} - flood limit, sleep {e.timeout} seconds")
        await asyncio.sleep(e.timeout)
        return await broadcast_schedule(user_id, message_type)
    except exceptions.UserDeactivated:
        db.del_user(user_id)
        logging.error(f"target id:{user_id} - user is deactivated")
    except exceptions.TelegramAPIError:
        logging.exception(f"target id:{user_id} - failed")
    else:
        logging.info(f"target id:{user_id}: success")
        return True
    return False


async def broadcast_message(user_id: int, message: Message, message_type: str):
    try:
        if message_type in "copy":
            await message.send_copy(user_id, disable_notification=True,
                                    reply_markup=keyboards.kb_main)
        elif message_type in "forward":
            await message.forward(user_id, disable_notification=True)

    except exceptions.BotBlocked:
        logging.error(f"target id:{user_id} - blocked by user")
        db.del_user(user_id)
    except exceptions.ChatNotFound:
        db.del_user(user_id)
        logging.error(f"target id:{user_id} - chat not found")
    except exceptions.RetryAfter as e:
        logging.error(f"target id:{user_id} - flood limit, sleep {e.timeout} seconds")
        await asyncio.sleep(e.timeout)
        return await broadcast_message(user_id, message, message_type)
    except exceptions.UserDeactivated:
        db.del_user(user_id)
        logging.error(f"target id:{user_id} - user is deactivated")
    except exceptions.TelegramAPIError:
        logging.exception(f"target id:{user_id} - failed")
    else:
        logging.info(f"target id:{user_id}: success")
        return True
    return False
