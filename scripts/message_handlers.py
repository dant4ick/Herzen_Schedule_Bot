import asyncio
import logging
import random
from datetime import timedelta
from typing import List, Callable

from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import exceptions

from scripts import keyboards
from scripts.bot import db, bot
from scripts.parse import parse_date_schedule
from scripts.utils import validate_user, seconds_before_iso_time, generate_schedule_message, today_for_group

TELEGRAM_MESSAGE_MAX_LEN = 4000
SCHEDULE_CHUNK_BODY_LEN = 3300
SCHEDULE_CHUNK_DELAY_SECONDS = 0.6


def _split_text_into_chunks(text: str, max_len: int) -> List[str]:
    if len(text) <= max_len:
        return [text]

    chunks: List[str] = []
    current_lines: List[str] = []
    current_len = 0

    for line in text.splitlines(keepends=True):
        line_len = len(line)
        if line_len > max_len:
            if current_lines:
                chunks.append("".join(current_lines).rstrip("\n"))
                current_lines = []
                current_len = 0
            for start in range(0, line_len, max_len):
                chunks.append(line[start:start + max_len].rstrip("\n"))
            continue

        if current_lines and current_len + line_len > max_len:
            chunks.append("".join(current_lines).rstrip("\n"))
            current_lines = [line]
            current_len = line_len
            continue

        current_lines.append(line)
        current_len += line_len

    if current_lines:
        chunks.append("".join(current_lines).rstrip("\n"))

    return [chunk for chunk in chunks if chunk]


def _build_schedule_messages(header: str, period: str, schedule_text: str, reminder: str) -> List[str]:
    body_chunks = _split_text_into_chunks(schedule_text, SCHEDULE_CHUNK_BODY_LEN)
    total_parts = len(body_chunks)

    messages = []
    for index, chunk in enumerate(body_chunks, start=1):
        if index == 1:
            text = f"{header}\n\nВот твое расписание на {period}:\n{chunk}"
        else:
            text = f"<i>Продолжение расписания ({index}/{total_parts})</i>\n{chunk}"
        messages.append(text)

    if reminder:
        if len(messages[-1]) + len(reminder) <= TELEGRAM_MESSAGE_MAX_LEN:
            messages[-1] += reminder
        else:
            messages.append(reminder)

    return messages


async def handle_broadcast_exceptions(user_id: int, e: exceptions.TelegramAPIError, retry_callback: Callable):
    if isinstance(e, exceptions.TelegramForbiddenError):
        logging.error(f"target id:{user_id} - forbidden")
        db.del_user(user_id)
    elif isinstance(e, exceptions.TelegramNotFound) or isinstance(e, exceptions.TelegramBadRequest):
        db.del_user(user_id)
        logging.error(f"target id:{user_id} - chat not found")
    elif isinstance(e, exceptions.TelegramRetryAfter):
        logging.error(f"target id:{user_id} - flood limit, sleep {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        return await retry_callback()
    elif isinstance(e, exceptions.TelegramAPIError):
        logging.exception(f"target id:{user_id} - failed")


async def send_date_schedule(
    user_id: int,
    schedule_response,
    period: str,
    header: str = "",
    buttons: List[InlineKeyboardButton] | None = None,
):
    logging.debug(f"response: {schedule_response}")

    if schedule_response is None:
        return
    
    schedule, url = schedule_response

    inline_keyboard = [[InlineKeyboardButton(text='Проверить на сайте', url=f"{url}")]]
    if buttons:
        inline_keyboard.append(buttons)
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    if schedule is None:
        await bot.send_message(user_id, f"{header}\n\n😖 Упс, кажется, расписание не отвечает. Попробуй еще раз.\n"
                                           f"Если на сайте по кнопке ниже тоже ничего не работает, бот тут ни при чем. "
                                           f"Если сайт показывает все исправно, напиши админу - ссылка в профиле бота.",
                                  reply_markup=reply_markup)
        logging.error(f"failed to get schedule for user {user_id}")
        return

    if random.randint(0, 100) < 5:
        reminder = "<i>\n😉 Не забывай про возможность поддержать разработчика через /donate.</i>"
    elif random.randint(0, 100) < 10:
        reminder = "<i>\n🤖 Нравится бот? Расскажи про него другим:\n</i>" \
                   r"https://t.me/schedule_herzen_bot"
    else:
        reminder = ""

    if "недел" in period:
        if "эта" in period:
            period = "этой неделе"
        else:
            period = "следующей неделе"

    if not schedule:
        await bot.send_message(user_id, f"{header}\n\n"
                                           f"🎉 На {period} занятий нет, можно отдыхать.\n"
                                           f"{reminder}",
                                  reply_markup=reply_markup)
        await asyncio.sleep(0.5)
        await bot.send_sticker(user_id, await get_random_chill_sticker())
        return

    if "недел" in period:
        if "этой" in period:
            period = "эту неделю"
        else:
            period = "следующую неделю"

    msg_text = await generate_schedule_message(schedule)
    full_message = f"{header}\n\nВот твое расписание на {period}:\n{msg_text}{reminder}"

    if len(full_message) <= TELEGRAM_MESSAGE_MAX_LEN:
        await bot.send_message(user_id, full_message, reply_markup=reply_markup)
        return

    split_messages = _build_schedule_messages(
        header=header,
        period=period,
        schedule_text=msg_text,
        reminder=reminder,
    )
    logging.info("schedule message split into %s parts for user %s", len(split_messages), user_id)

    for index, message_text in enumerate(split_messages):
        await bot.send_message(
            user_id,
            message_text,
            reply_markup=reply_markup if index == len(split_messages) - 1 else None,
        )
        if index < len(split_messages) - 1:
            await asyncio.sleep(SCHEDULE_CHUNK_DELAY_SECONDS)


async def mailing_schedule(mailing_time: str, schedule_date: str):
    while True:
        pause = await seconds_before_iso_time(mailing_time)

        await asyncio.sleep(pause)
        logging.info(f"starting to mail schedules")
        mailing_list = db.get_mailing_list()
        for user_id, mailing_time in mailing_list:
            try:
                await broadcast_schedule(user_id, message_type=schedule_date)
            except asyncio.TimeoutError:
                logging.error(f"Timeout error occurred while broadcasting schedule to user {user_id}")
            await asyncio.sleep(.5)
        await asyncio.sleep(1)


async def broadcast_schedule(user_id: int, message_type: str):
    try:
        if not await validate_user(user_id):
            logging.info(f"user validation failed during mailing - id: {user_id}")
            return
        group_id, sub_group = db.get_user(user_id)

        header_text = "👋 Привет, это рассылка расписания."

        if message_type in "today":
            today = today_for_group(group_id)

            logging.info(f"attempted to mail today schedule - id: {user_id}")

            schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=today)
            await send_date_schedule(user_id, schedule_response, "сегодня",
                                     header=header_text, buttons=[keyboards.inline_bt_unsub])
        elif message_type in "tomorrow":
            tomorrow = today_for_group(group_id) + timedelta(days=1)

            logging.info(f"attempted to mail tomorrow schedule - id: {user_id}")

            schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=tomorrow)
            await send_date_schedule(user_id, schedule_response, "завтра",
                                     header=header_text, buttons=[keyboards.inline_bt_unsub])
    except exceptions.TelegramAPIError as e:
        await handle_broadcast_exceptions(user_id, e, lambda: broadcast_schedule(user_id, message_type))
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
    except exceptions.TelegramAPIError as e:
        await handle_broadcast_exceptions(user_id, e, lambda: broadcast_message(user_id, message, message_type))
    else:
        logging.info(f"target id:{user_id}: success")
        return True
    return False


async def get_random_chill_sticker():
    stickers = [
        'CAACAgIAAxkBAAEXjKZjC-Ky4494QMqmyAKgvTFV4fsJdQACoAwAAnUY2Et2hyIlXw_lYSkE',  # Blue cat party
        'CAACAgIAAxkBAAEXpeFjD6_B6sT32S6khtedymBXcFiVjgAC3goAAjHH2EuOfaJNnbW_JykE',  # Blue cat chill
        'CAACAgIAAxkBAAEXpd1jD6-6pRbe-UgQ2C_2vNtccmNnbwACzRMAAl6zyEvD5PzG428z7ykE',  # Real cat vibing
        'CAACAgIAAxkBAAEXpdtjD6-dRMqPJRtw405KJlvIcFiPVwACRBQAAgyeKEjz0Nb_G-GZ4SkE',  # Emoji party
        'CAACAgIAAxkBAAEXpd9jD6-9IxLBW0nmsjZ3_EYm8Q9dSgACIhQAAraw0EtoiZUwd4T4UykE',  # Pear party
        'CAACAgIAAxkBAAEXpeNjD6_GQ3TKcVOe0oKVNJoygASHXwACbQEAAiI3jgQl87gUwpqm8ikE',  # Kolobok party
        'CAACAgIAAxkBAAEf9txkQA2ZDDdefP6poUYQUQ9iE3AL3AAC7hMAAhljSElGyHkrfgiHTC8E',  # Minecraft piglin
    ]
    return stickers[random.randint(0, len(stickers) - 1)]
