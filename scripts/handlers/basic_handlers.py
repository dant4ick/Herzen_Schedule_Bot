import logging
import re
from datetime import datetime, timedelta

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command, CommandObject

from scripts.bot import db, dp
from scripts import keyboards
from scripts.parse import parse_date_schedule
from scripts.utils import validate_user, get_dates_regexp, date_range_pattern, year_pattern
from scripts.message_handlers import send_date_schedule


@dp.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer(f"Привет, я <b>Herzen Schedule Bot</b>! "
                     f"Смогу помочь тебе быстро узнать твое <b>расписание</b>.\n"
                     f"Для этого тебе нужно пройти опрос, чтобы я знал, где ты учишься. "
                     f"На клавиатуре у тебя появилась кнопка <b>{keyboards.bt_group_config.text}</b>.\n"
                     f"Нажимай и давай начинать! Если промахнешься по кнопкам, снизу всегда есть \"Отмена\"",
                     reply_markup=keyboards.kb_settings)
    logging.info(f"start: {msg.from_user.id} (@{msg.from_user.username})")


@dp.message(Command('help'))
async def get_help(msg: types.Message):
    await msg.answer(f"Чтобы посмотреть расписание, используй кнопки "
                     f"{keyboards.bt_schedule_today.text}, {keyboards.bt_schedule_tomorrow.text}, "
                     f"{keyboards.bt_schedule_curr_week.text}, {keyboards.bt_schedule_next_week.text}.\n\n"
                     f"Интересует конкретная дата или период? Попробуй /date.\n\n"
                     f"Чтобы изменить свою группу, настроить рассылку, заходи в {keyboards.bt_settings.text}.\n\n"
                     f"Что-то не понятно? Столкнулись с проблемой? "
                     f"По любому поводу можешь написать разработчику, ссылка есть в описании бота.\n\n"
                     f"Хочешь поддержать бота и его разработчика - /donate",
                     reply_markup=keyboards.kb_main)


@dp.message(Command('hide'))
# @dp.throttled(throttled, rate=2)
async def hide_keyboard(msg: types.Message):
    await msg.answer("Окей, клавиатура скрыта. Чтобы вернуть ее, используй /show.",
                     reply_markup=ReplyKeyboardRemove())


@dp.message(Command('show'))
# @dp.throttled(throttled, rate=2)
async def show_keyboard(msg: types.Message):
    await msg.answer("Окей, вернул клавиатуру. Чтобы скрыть ее, используй /hide.",
                     reply_markup=keyboards.kb_main)


@dp.message(F.text.regexp(get_dates_regexp()))
@dp.message(Command('date'))
# @dp.throttled(throttled, rate=5)
async def send_specific_date_schedule(msg: types.Message, command: CommandObject = None):
    if not await validate_user(msg.from_user.id):
        logging.info(f"user validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return

    args: str = command.args if command else msg.text
    if not args:
        await msg.answer("Чтобы вывести расписание на конкретную <b>дату</b>, напиши:\n"
                         "<code>ДД.ММ.ГГГГ</code> <i>(год можно не писать)</i>\n\n"
                         "Чтобы вывести расписание на конкретный <b>период</b>, напиши:\n"
                         "<code>ДД.MM.ГГГГ-ДД.MM.ГГГГ</code> <i>(год можно не писать)</i>\n\n"
                         "Можешь попробовать несколько дат или периодов через пробел, должно сработать!\n\n"
                         "Правила такие: максимум 4 даты/периода за запрос, не больше двух периодов в одном запросе.")
        return

    matches = re.findall(get_dates_regexp(), args)
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


@dp.message(F.text == keyboards.bt_schedule_today.text)
# @dp.throttled(throttled, rate=2)
async def send_today_schedule(msg: types.Message):
    if not await validate_user(msg.from_user.id):
        logging.info(f"user validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    today = datetime.today().date()

    logging.info(f"attempted send today schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=today)

    await send_date_schedule(msg.from_user.id, schedule_response, "сегодня")


@dp.message(F.text == keyboards.bt_schedule_tomorrow.text)
# @dp.throttled(throttled, rate=2)
async def send_tomorrow_schedule(msg: types.Message):
    if not await validate_user(msg.from_user.id):
        logging.info(f"user validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return
    group_id, sub_group = db.get_user(msg.from_user.id)

    tomorrow = datetime.today().date() + timedelta(days=1)

    logging.info(f"attempted send tomorrow schedule - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    schedule_response = await parse_date_schedule(group=group_id, sub_group=sub_group, date_1=tomorrow)

    await send_date_schedule(msg.from_user.id, schedule_response, "завтра")


@dp.message(F.text == keyboards.bt_schedule_curr_week.text)
# @dp.throttled(throttled, rate=5)
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


@dp.message(F.text == keyboards.bt_schedule_next_week.text)
# @dp.throttled(throttled, rate=5)
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
