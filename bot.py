from datetime import datetime

from aiogram.dispatcher import filters
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import TELEGRAM_TOKEN
from parse import *
import logging

from aiogram import Bot, Dispatcher, executor, types

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)


@dp.message_handler(filters.Text(contains='выбрать группу', ignore_case=True))
async def send_today_schedule(msg: types.Message):
    with open('groups.json', 'r', encoding='UTF-8') as groups_json:
        groups = json.load(groups_json)

    msg_text = ''
    counter = 1
    inline_kb_numbers = InlineKeyboardMarkup(row_width=8)
    for faculty in groups.keys():
        msg_text += f"{counter}. {faculty[0].upper()+faculty[1:]}\n"
        inline_kb_numbers.insert(InlineKeyboardButton(f'{counter}', callback_data=f'{counter}'))
        counter += 1

    await msg.answer(f"<b>На клавиатуре ниже выберите цифру, соответствующую вашему факультету:</b>\n\n"
                     f"{msg_text}",
                     reply_markup=inline_kb_numbers)


async def generate_schedule_message(schedule):
    msg_text = ''
    for course in schedule[list(schedule.keys())[0]]:
        msg_text += f"\n⏰ {course['time']}" \
                    f"\n<b>{course['name']}</b> {course['type']}" \
                    f"\n{course['teacher']}" \
                    f"\n{course['room']}\n"
    return msg_text


@dp.message_handler(commands=['today'])
async def send_today_schedule(msg: types.Message):
    if not msg.get_args():
        await msg.answer("Кажется, я не знаю, где ты учишься. "
                         "Пройди опрос, чтобы я мог вывести твое расписание.")
        return

    today = datetime.today().date()
    schedule = parse_date_schedule(group=msg.get_args(), sub_group=2, date_1=today)
    if not schedule:
        await msg.answer("Сегодня занятий нет, можно отдыхать.")
        return

    msg_text = generate_schedule_message(schedule)
    await msg.answer(f"Вот твое расписание на {today}:\n{msg_text}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
