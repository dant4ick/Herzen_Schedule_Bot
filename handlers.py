from datetime import datetime

from aiogram import types

from bot import db, dp
from parse import parse_date_schedule
from utils import generate_schedule_message


@dp.message_handler(commands=['today'])
async def send_today_schedule(msg: types.Message):
    group_id, sub_group = db.get_user(msg.from_user.id)
    if not group_id:
        await msg.answer("Кажется, я не знаю, где ты учишься. "
                         "Пройди опрос, чтобы я мог вывести твое расписание.")
        return

    today = datetime.today().date()
    schedule = parse_date_schedule(group=group_id, sub_group=sub_group, date_1=today)
    if not schedule:
        await msg.answer("Сегодня занятий нет, можно отдыхать.")
        return

    msg_text = generate_schedule_message(schedule)
    await msg.answer(f"Вот твое расписание на {today}:\n{msg_text}")