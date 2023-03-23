import logging
import re
from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove

from scripts.bot import db, dp
from scripts import keyboards
from scripts.parse import parse_date_schedule
from scripts.utils import validate_user, throttled
from scripts.message_handlers import send_date_schedule


@dp.message_handler(commands=['start'], state='*')
async def start(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer("Привет, я <b>Herzen Schedule Bot</b>! "
                     "Смогу помочь тебе быстро узнать твое <b>расписание</b>.\n"
                     "Для этого тебе нужно пройти опрос, чтобы я знал, где ты учишься. "
                     "На клавиатуре у тебя появилась кнопка \"Настройка группы\".\n"
                     "Нажимай и давай начинать! Если промахнешься по кнопкам, снизу всегда есть \"Отмена\"",
                     reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(keyboards.bt_group_config))
    logging.info(f"start: {msg.from_user.id} (@{msg.from_user.username})")


@dp.message_handler(commands=['help'])
async def get_help(msg: types.Message):
    await msg.answer("Чтобы посмотреть расписание, используй кнопки \"Сегодня\", \"Завтра\", "
                     "\"Эта неделя\", \"Следующая неделя\".\n\n"
                     "Интересует конкретная дата или период? Попробуй /date.\n\n"
                     "Чтобы изменить свою группу, настроить рассылку, заходи в \"Настройки\".\n\n"
                     "Что-то не понятно? Столкнулись с проблемой? "
                     "По любому поводу можешь написать разработчику, ссылка есть в описании бота.\n\n"
                     "Хочешь поддержать бота и его разработчика - /donate",
                     reply_markup=keyboards.kb_main)


@dp.message_handler(commands=['hide'])
@dp.throttled(throttled, rate=2)
async def hide_keyboard(msg: types.Message):
    await msg.answer("Окей, клавиатура скрыта. Чтобы вернуть ее, используй /show.",
                     reply_markup=ReplyKeyboardRemove())


@dp.message_handler(commands=['show'])
@dp.throttled(throttled, rate=2)
async def show_keyboard(msg: types.Message):
    await msg.answer("Окей, вернул клавиатуру. Чтобы скрыть ее, используй /hide.",
                     reply_markup=keyboards.kb_main)


@dp.message_handler(commands=['date'])
@dp.throttled(throttled, rate=5)
async def send_specific_date_schedule(msg: types.Message):
    if not await validate_user(msg.from_user.id):
        logging.info(f"user validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return

    args = msg.get_args()
    if not args:
        await msg.answer("Чтобы вывести расписание на конкретную <b>дату</b>, напиши:\n"
                         "<code>/date ДД.ММ.ГГГГ</code> <i>(год можно не писать)</i>\n\n"
                         "Чтобы вывести расписание на конкретный <b>период</b>, напиши:\n"
                         "<code>/date ДД.MM.ГГГГ-ДД.MM.ГГГГ</code> <i>(год можно не писать)</i>\n\n"
                         "Можешь попробовать после команды <code>/date</code> "
                         "написать несколько дат или периодов через пробел, должно сработать!\n"
                         "Правила такие: максимум 4 даты/периода за запрос, не больше двух периодов в одном запросе.")
        return

    day_pattern = r"(\b((0[1-9])|([1-2]\d)|(3[0-1])|([1-9])))"
    month_pattern = r"(\.((0[1-9])|(1[0-2])|([1-9]))\b)"
    year_pattern = r"(\.(\d{4}))"
    date_pattern = r"({0}{1}({2})?)".format(day_pattern, month_pattern, year_pattern)
    date_range_pattern = r"({0}\-{1})".format(date_pattern, date_pattern)
    matches = re.findall(r"((\A|\s|\b)({r}|{d})(\Z|\s))".format(r=date_range_pattern, d=date_pattern), args)
    dates = [date[0].strip() for date in matches]

    if not dates:
        await msg.answer(f"Проверь, что ты ввел дату в правильном формате. Чтобы получить помощь, жми /date.")
        return
    if len(dates) > 4:
        await msg.answer(f"Прости, но я не поддерживаю больше, чем 4 даты/периода за один запрос.")
        return

    dates_formatted = []
    dates_range_formatted = []
    for date in dates:
        try:
            if re.search(date_range_pattern, date):
                date_range = date.split("-")
                for date_range_part in date_range:
                    part_index = date_range.index(date_range_part)
                    if not re.search(year_pattern, date_range_part):
                        date_range_part += f".{datetime.now().year}"
                    day, month, year = date_range_part.split(".")
                    date_range[part_index] = datetime.strptime(f"{day.zfill(2)}.{month.zfill(2)}.{year}",
                                                               "%d.%m.%Y").date()
                dates_range_formatted.append(date_range)
            else:
                if not re.search(year_pattern, date):
                    date += f".{datetime.now().year}"
                day, month, year = date.split(".")
                dates_formatted.append(datetime.strptime(f"{day.zfill(2)}.{month.zfill(2)}.{year}", "%d.%m.%Y").date())
        except ValueError:
            await msg.answer(f"Не получится посмотреть расписание на ({date})")

    group_id, sub_group = db.get_user(msg.from_user.id)

    for single_date in dates_formatted:
        schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=single_date)
        await send_date_schedule(msg.from_user.id, schedule_response, single_date.strftime("(%d.%m.%Y)"))

    if len(dates_range_formatted) > 2:
        await msg.answer(f"Я не поддерживаю больше, чем 2 периода за один запрос. Вывожу первые два...")
        dates_range_formatted = dates_range_formatted[:2]

    for dates_range in dates_range_formatted:
        days_range = (dates_range[1] - dates_range[0]).days
        if days_range < 0:
            await msg.answer(f"Первая дата ({dates_range[0].strftime('%d.%m.%Y')}) "
                             f"больше, чем вторая ({dates_range[1].strftime('%d.%m.%Y')}).")
            continue
        if days_range > 8:
            await msg.answer(f"Период ({dates_range[0].strftime('%d.%m.%Y')} - "
                             f"{dates_range[1].strftime('%d.%m.%Y')}) больше восьми дней.\n"
                             f"Попробуй разделить его на несколько периодов.")
            continue
        schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group,
                                                      date_1=dates_range[0], date_2=dates_range[1])
        await send_date_schedule(msg.from_user.id, schedule_response, f'({dates_range[0].strftime("%d.%m.%Y")} - '
                                                                      f'{dates_range[1].strftime("%d.%m.%Y")})')


@dp.message_handler(filters.Text(contains='сегодня', ignore_case=True))
@dp.throttled(throttled, rate=2)
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
@dp.throttled(throttled, rate=2)
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
@dp.throttled(throttled, rate=5)
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
@dp.throttled(throttled, rate=5)
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
