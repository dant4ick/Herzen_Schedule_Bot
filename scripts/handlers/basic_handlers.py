import logging
from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from scripts.bot import db, dp
from scripts.handlers import keyboards
from scripts.parse import parse_date_schedule
from scripts.utils import generate_schedule_message, validate_user, get_random_chill_sticker


@dp.message_handler(commands=['start'], state='*')
async def start(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer("Привет, я <b>Herzen Schedule Bot</b>! "
                     "Смогу помочь тебе быстро узнать твое <b>расписание</b>.\n"
                     "Для этого тебе нужно пройти опрос, чтобы я знал, где ты учишься. "
                     "На клавиатуре у тебя появилась кнопка \"Настройка группы\".\n"
                     "Нажимай и давай начинать!",
                     reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(keyboards.bt_group_config))
    logging.info(f"start: {msg.from_user.id} (@{msg.from_user.username})")


@dp.message_handler(commands=['help'])
async def get_help(msg: types.Message):
    await msg.answer("Чтобы посмотреть расписание, используй кнопки \"Сегодня\", \"Завтра\", \"Неделя\".\n"
                     "Чтобы изменить свою группу, используй кнопку \"Настройка группы\".\n"
                     "Что-то не понятно? Столкнулись с проблемой? "
                     "По любому поводу можешь написать разработчику, ссылка есть в описании бота. "
                     "Не кусаюсь 😉",
                     reply_markup=keyboards.kb_main)


async def send_date_schedule(msg: types.Message, schedule_response, period: str):
    logging.info(f"response: {schedule_response}")

    if schedule_response is None:
        await msg.answer("😖 Упс, кажется, расписание не отвечает. Попробуй еще раз.")

    if period == "неделя":
        period = "этой неделе"

    if not schedule_response:
        await msg.answer(f"🎉На {period} занятий нет, можно отдыхать.")
        await msg.answer_sticker(await get_random_chill_sticker())
        return

    schedule, url = schedule_response

    if period == "этой неделе":
        period = "эту неделю"

    msg_text = await generate_schedule_message(schedule)
    await msg.answer(f"Вот твое расписание на {period}:\n{msg_text}",
                     reply_markup=InlineKeyboardMarkup().add(
                         InlineKeyboardButton('Проверить на сайте', f"{url}")
                     ))


@dp.message_handler(filters.Text(contains='сегодня', ignore_case=True))
async def send_today_schedule(msg: types.Message):
    if not await validate_user(msg):
        logging.info(f"User validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    today = datetime.today().date()

    logging.info(f"Attempted send today schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=today)

    await send_date_schedule(msg, schedule_response, "сегодня")


@dp.message_handler(filters.Text(contains='завтра', ignore_case=True))
async def send_tomorrow_schedule(msg: types.Message):
    if not await validate_user(msg):
        logging.info(f"User validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    tomorrow = datetime.today().date() + timedelta(days=1)

    logging.info(f"Attempted send tomorrow schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=tomorrow)

    await send_date_schedule(msg, schedule_response, "завтра")


@dp.message_handler(filters.Text(contains='неделя', ignore_case=True))
async def send_week_schedule(msg: types.Message):
    if not await validate_user(msg):
        logging.info(f"User validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    today = datetime.today().date()
    week = today + timedelta(days=6)

    logging.info(f"Attempted send week schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=today, date_2=week)

    await send_date_schedule(msg, schedule_response, "неделя")
