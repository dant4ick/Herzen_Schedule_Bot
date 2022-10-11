import logging
from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import ReplyKeyboardMarkup

from scripts.bot import db, dp
from scripts import keyboards
from scripts.parse import parse_date_schedule
from scripts.utils import validate_user, send_date_schedule


@dp.message_handler(commands=['start'], state='*')
async def start(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer("Привет, я <b>Herzen Schedule Bot</b>! "
                     "Смогу помочь тебе быстро узнать твое <b>расписание</b>.\n"
                     "Для этого тебе нужно пройти опрос, чтобы я знал, где ты учишься. "
                     "На клавиатуре у тебя появилась кнопка \"Настройка группы\".\n"
                     "Нажимай и давай начинать! Если промахнешься по кнопкам, снизу всегда есть \"Отмена\"",
                     reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(keyboards.bt_settings))
    logging.info(f"start: {msg.from_user.id} (@{msg.from_user.username})")


@dp.message_handler(commands=['help'])
async def get_help(msg: types.Message):
    await msg.answer("Чтобы посмотреть расписание, используй кнопки \"Сегодня\", \"Завтра\", "
                     "\"Эта неделя\", \"Следующая неделя\".\n"
                     "Чтобы изменить свою группу, используй кнопку \"Настройка группы\".\n"
                     "Что-то не понятно? Столкнулись с проблемой? "
                     "По любому поводу можешь написать разработчику, ссылка есть в описании бота. "
                     "Не кусаюсь 😉",
                     reply_markup=keyboards.kb_main)


@dp.message_handler(filters.Text(contains='сегодня', ignore_case=True))
async def send_today_schedule(msg: types.Message):
    if not await validate_user(msg.from_user.id):
        logging.info(f"user validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    today = datetime.today().date()

    logging.info(f"attempted send today schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=today)

    await send_date_schedule(msg.from_user.id, schedule_response, "сегодня")


@dp.message_handler(filters.Text(contains='завтра', ignore_case=True))
async def send_tomorrow_schedule(msg: types.Message):
    if not await validate_user(msg.from_user.id):
        logging.info(f"user validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    tomorrow = datetime.today().date() + timedelta(days=1)

    logging.info(f"attempted send tomorrow schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=tomorrow)

    await send_date_schedule(msg.from_user.id, schedule_response, "завтра")


@dp.message_handler(filters.Text(contains='эта неделя', ignore_case=True))
async def send_curr_week_schedule(msg: types.Message):
    if not await validate_user(msg.from_user.id):
        logging.info(f"user validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    today = datetime.today().date()

    week_first = today - timedelta(days=today.weekday())
    week_last = week_first + timedelta(days=6)

    logging.info(f"attempted send curr week schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group,
                                                  date_1=week_first, date_2=week_last)

    await send_date_schedule(msg.from_user.id, schedule_response, "эта неделя")


@dp.message_handler(filters.Text(contains='следующая неделя', ignore_case=True))
async def send_next_week_schedule(msg: types.Message):
    if not await validate_user(msg.from_user.id):
        logging.info(f"user validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    today = datetime.today().date()

    week_first = today - timedelta(days=today.weekday()) + timedelta(days=7)
    week_last = week_first + timedelta(days=6)

    logging.info(f"attempted send next week schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group,
                                                  date_1=week_first, date_2=week_last)

    await send_date_schedule(msg.from_user.id, schedule_response, "следующая неделя")
