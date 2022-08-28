from aiogram import types
from aiogram.dispatcher import FSMContext, filters
from aiogram.types import CallbackQuery

import states
from bot import dp, db
from utils import *


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

    db.add_user(call.from_user.id, group_id)

    await call.message.edit_text(f"<b>Хорошо, теперь можно исполь</b>")
    await states.UserData.next()