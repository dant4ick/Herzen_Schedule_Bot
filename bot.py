from datetime import datetime

from aiogram.dispatcher import filters, FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData

import states
from config import TELEGRAM_TOKEN
from parse import *
import logging

from aiogram import Bot, Dispatcher, executor, types

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)

cb_data = CallbackData('data', 'num')


async def open_groups_file():
    with open('groups.json', 'r', encoding='UTF-8') as groups_json:
        groups = json.load(groups_json)
    return groups


async def generate_kb_nums(source):
    msg_text = ''
    counter = 1
    inline_kb_numbers = InlineKeyboardMarkup(row_width=8)
    for data in source.keys():  # Generating text + buttons
        msg_text += f"{counter}. {data[0].upper() + data[1:]}\n"
        inline_kb_numbers.insert(InlineKeyboardButton(f'{counter}', callback_data=cb_data.new(num=counter)))
        counter += 1
    return msg_text, inline_kb_numbers


@dp.callback_query_handler(text='cancel', state='*')
async def cancel_process(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.reply("Ok, let's forget about it.")
    await call.message.delete_reply_markup()
    await call.answer()


@dp.message_handler(filters.Text(contains='выбрать группу', ignore_case=True))
async def set_faculty(msg: types.Message):
    groups = await open_groups_file()

    msg_text, inline_kb_numbers = await generate_kb_nums(groups)

    await msg.answer(f"<b>На клавиатуре ниже выберите цифру, соответствующую вашему факультету:</b>\n\n"
                     f"{msg_text}",
                     reply_markup=inline_kb_numbers)
    await states.UserData.Faculty.set()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Faculty)
async def set_form(call: CallbackQuery, callback_data: dict, state: FSMContext):
    groups = await open_groups_file()
    faculty_name = list(groups.keys())[int(callback_data['num']) - 1]
    forms = groups[faculty_name]
    async with state.proxy() as data:
        data['faculty'] = faculty_name

    msg_text, inline_kb_numbers = await generate_kb_nums(forms)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашей форме обучения:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers)
    await states.UserData.next()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Form)
async def set_step(call: CallbackQuery, callback_data: dict, state: FSMContext):
    groups = await open_groups_file()

    async with state.proxy() as data:
        faculty_name = data['faculty']
        form_name = list(groups[faculty_name].keys())[int(callback_data['num']) - 1]
        data['form'] = form_name

    steps = groups[faculty_name][form_name]

    msg_text, inline_kb_numbers = await generate_kb_nums(steps)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашей ступени обучения:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers)
    await states.UserData.next()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Step)
async def set_step(call: CallbackQuery, callback_data: dict, state: FSMContext):
    groups = await open_groups_file()

    async with state.proxy() as data:
        faculty_name = data['faculty']
        form_name = data['form']
        step_name = list(groups[faculty_name][form_name].keys())[int(callback_data['num']) - 1]
        data['step'] = step_name

    courses = groups[faculty_name][form_name][step_name]

    msg_text, inline_kb_numbers = await generate_kb_nums(courses)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашему году обучения:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers)
    await states.UserData.next()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Course)
async def set_step(call: CallbackQuery, callback_data: dict, state: FSMContext):
    groups = await open_groups_file()

    async with state.proxy() as data:
        faculty_name = data['faculty']
        form_name = data['form']
        step_name = data['step']
        course_name = list(groups[faculty_name][form_name][step_name].keys())[int(callback_data['num']) - 1]
        data['course'] = course_name

    groups = groups[faculty_name][form_name][step_name][course_name]

    msg_text, inline_kb_numbers = await generate_kb_nums(groups)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашей группе:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers)
    await states.UserData.next()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Group)
async def set_step(call: CallbackQuery, callback_data: dict, state: FSMContext):
    groups = await open_groups_file()

    async with state.proxy() as data:
        faculty_name = data['faculty']
        form_name = data['form']
        step_name = data['step']
        course_name = data['course']
        group_name = list(groups[faculty_name][form_name][step_name][course_name].keys())[int(callback_data['num']) - 1]

    group_id = groups[faculty_name][form_name][step_name][course_name][group_name]

    await call.message.edit_text(f"<b>Айдишник группы: {group_id}</b>")
    await states.UserData.next()


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
