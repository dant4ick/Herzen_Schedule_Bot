import json

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

import keyboard
from bot import db

cb_data = CallbackData('data', 'num')


async def open_groups_file():
    with open('groups.json', 'r', encoding='UTF-8') as groups_json:
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
    for course in schedule[list(schedule.keys())[0]]:
        msg_text += f"\n⏰ {course['time']}" \
                    f"\n<b>{course['name']}</b> {course['type']}" \
                    f"\n{course['teacher']}" \
                    f"\n{course['room']}\n"
    return msg_text


async def validate_user(msg):
    user_data = db.get_user(msg.from_user.id)
    if not user_data:
        await msg.answer("Кажется, я не знаю, где ты учишься. "
                         "Пройди опрос, чтобы я мог вывести твое расписание.",
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(keyboard.bt_group_config))
        return False
    return True
