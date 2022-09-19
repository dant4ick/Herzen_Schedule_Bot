import logging

from aiogram import types
from aiogram.dispatcher import FSMContext, filters
from aiogram.types import CallbackQuery

from scripts.handlers import basic_handlers
from scripts import states
from scripts.bot import dp
from scripts.utils import *


@dp.callback_query_handler(text='cancel', state='*')
async def cancel_process_cb(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.reply("Хорошо, забыли.")
    await call.message.delete_reply_markup()
    await call.answer()


@dp.message_handler(filters.Text(contains='настройка группы', ignore_case=True))
async def start_config(msg: types.Message):
    groups = await open_groups_file()

    logging.info(f"{msg.from_user.id} (@{msg.from_user.username})")

    msg_text, inline_kb_numbers = await generate_kb_nums(groups)

    await msg.answer(f"<b>На клавиатуре ниже выберите цифру, соответствующую вашему факультету:</b>\n\n"
                     f"{msg_text}",
                     reply_markup=inline_kb_numbers
                     .row(InlineKeyboardButton('Отменить', callback_data='cancel')))
    await states.UserData.Faculty.set()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Faculty)
async def set_faculty(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()
    faculty_name = list(groups.keys())[int(callback_data['num']) - 1]
    forms = groups[faculty_name]
    async with state.proxy() as data:
        data['faculty'] = faculty_name

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {faculty_name}")

    msg_text, inline_kb_numbers = await generate_kb_nums(forms)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашей форме обучения:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers
                                 .row(InlineKeyboardButton('Отменить', callback_data='cancel')))
    await states.UserData.next()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Form)
async def set_form(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()

    async with state.proxy() as data:
        faculty_name = data['faculty']
        form_name = list(groups[faculty_name].keys())[int(callback_data['num']) - 1]
        data['form'] = form_name

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {form_name}")

    steps = groups[faculty_name][form_name]

    msg_text, inline_kb_numbers = await generate_kb_nums(steps)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашей ступени обучения:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers
                                 .row(InlineKeyboardButton('Отменить', callback_data='cancel')))
    await states.UserData.next()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Step)
async def set_step(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()

    async with state.proxy() as data:
        faculty_name = data['faculty']
        form_name = data['form']
        step_name = list(groups[faculty_name][form_name].keys())[int(callback_data['num']) - 1]
        data['step'] = step_name

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {step_name}")

    courses = groups[faculty_name][form_name][step_name]

    msg_text, inline_kb_numbers = await generate_kb_nums(courses)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашему году обучения:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers
                                 .row(InlineKeyboardButton('Отменить', callback_data='cancel')))
    await states.UserData.next()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Course)
async def set_course(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()

    async with state.proxy() as data:
        faculty_name = data['faculty']
        form_name = data['form']
        step_name = data['step']
        course_name = list(groups[faculty_name][form_name][step_name].keys())[int(callback_data['num']) - 1]
        data['course'] = course_name

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {course_name}")

    groups = groups[faculty_name][form_name][step_name][course_name]

    msg_text, inline_kb_numbers = await generate_kb_nums(groups)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашей группе:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers
                                 .row(InlineKeyboardButton('Отменить', callback_data='cancel')))
    await states.UserData.next()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.Group)
async def set_group(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()

    async with state.proxy() as data:
        faculty_name = data['faculty']
        form_name = data['form']
        step_name = data['step']
        course_name = data['course']
        group_name = list(groups[faculty_name][form_name][step_name][course_name].keys())[int(callback_data['num']) - 1]
        group_id = groups[faculty_name][form_name][step_name][course_name][group_name]
        data['group_id'] = group_id

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {group_name} ({group_id})")

    await call.message.edit_text("Если такая есть, выберите <b>номер подгруппы.</b> "
                                 "Если отсутствует, нажмите кнопку <b>\"Без подгруппы\"</b>.",
                                 reply_markup=InlineKeyboardMarkup().add(
                                     InlineKeyboardButton('Без подгруппы', callback_data=cb_data.new(num=0)),
                                     InlineKeyboardButton('1', callback_data=cb_data.new(num=1)),
                                     InlineKeyboardButton('2', callback_data=cb_data.new(num=2))
                                 ).row(
                                     InlineKeyboardButton('Отменить', callback_data='cancel')
                                 ))
    await states.UserData.next()


@dp.callback_query_handler(cb_data.filter(), state=states.UserData.SubGroup)
async def set_subgroup(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()

    async with state.proxy() as data:
        group_id = data['group_id']
        sub_group = int(callback_data['num'])

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {sub_group}")

    if sub_group not in range(3):
        logging.info(
            f"fail: {call.from_user.id} (@{call.from_user.username})")
        await call.message.edit_text("<b>Упс! Что-то пошло не так, пока мы устанавливали подгруппу...</b>\n"
                                     "Придется настроить заново 😓")
        await state.finish()
        return

    db.add_user(call.from_user.id, group_id, sub_group)

    await call.message.edit_text("<b>Хорошо, все готово!</b>\n"
                                 "Теперь можешь использовать кнопки, чтобы смотреть расписание!")
    await state.finish()
    logging.info(f"add: {call.from_user.id} (@{call.from_user.username})")
    await basic_handlers.get_help(call.message)
