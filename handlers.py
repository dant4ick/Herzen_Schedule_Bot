import logging
from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import filters
from aiogram.types import ReplyKeyboardMarkup

import keyboard
from bot import db, dp
from parse import parse_date_schedule
from utils import generate_schedule_message, validate_user, get_random_chill_sticker


@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await msg.answer("Привет, я <b>Herzen Schedule Bot</b>! "
                     "Смогу помочь тебе быстро узнать твое <b>расписание</b>.\n"
                     "Для этого тебе нужно пройти опрос, чтобы я знал, где ты учишься. "
                     "На клавиатуре у тебя появилась кнопка \"Настройка группы\".\n"
                     "Нажимай и давай начинать!",
                     reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(keyboard.bt_group_config))
    logging.info(f"Start: {msg.from_user.id} (@{msg.from_user.username})")


@dp.message_handler(commands=['help'])
async def get_help(msg: types.Message):
    await msg.answer("Чтобы посмотреть расписание, используй кнопки \"Сегодня\", \"Завтра\", \"Неделя\".\n"
                     "Чтобы изменить свою группу, используй кнопку \"Настройка группы\".",
                     reply_markup=keyboard.kb_main)


@dp.message_handler(filters.Text(contains='сегодня', ignore_case=True))
async def send_today_schedule(msg: types.Message):
    if not await validate_user(msg):
        logging.info(f"User validation failed - id: {msg.from_user.id}, username: {msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    today = datetime.today().date()
    schedule = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=today)

    logging.info(f"Attempted send today schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}\n"
                 f"response: {schedule}")

    if not schedule:
        await msg.answer("🎉 Сегодня занятий нет, можно отдыхать.")
        await msg.answer_sticker(await get_random_chill_sticker())
        return

    msg_text = await generate_schedule_message(schedule)
    await msg.answer(f"Вот твое расписание на сегодня:\n{msg_text}")


@dp.message_handler(filters.Text(contains='завтра', ignore_case=True))
async def send_tomorrow_schedule(msg: types.Message):
    if not await validate_user(msg):
        logging.info(f"User validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    tomorrow = datetime.today().date() + timedelta(days=1)
    schedule = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=tomorrow)

    logging.info(f"Attempted send tomorrow schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}\n"
                 f"response: {schedule}")

    if not schedule:
        await msg.answer("🎉 Завтра занятий нет, можно отдыхать.")
        await msg.answer_sticker(await get_random_chill_sticker())
        return

    msg_text = await generate_schedule_message(schedule)
    await msg.answer(f"Вот твое расписание на завтра:\n{msg_text}")


@dp.message_handler(filters.Text(contains='неделя', ignore_case=True))
async def send_week_schedule(msg: types.Message):
    if not await validate_user(msg):
        logging.info(f"User validation failed - id: {msg.from_user.id}, username: {msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    today = datetime.today().date()
    week = today + timedelta(days=6)

    schedule = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=today, date_2=week)

    logging.info(f"Attempted send week schedule - id: {msg.from_user.id}, username: {msg.from_user.username}\n"
                 f"response: {schedule}")

    if not schedule:
        await msg.answer("🎉 На неделе занятий нет, можно отдыхать.")
        await msg.answer_sticker(await get_random_chill_sticker())
        return

    msg_text = await generate_schedule_message(schedule)
    await msg.answer(f"Вот твое расписание на неделю :\n{msg_text}")
