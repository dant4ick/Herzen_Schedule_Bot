import logging

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from scripts.handlers import basic_handlers
from scripts import states
from scripts.utils import *
from scripts import keyboards


@dp.callback_query(F.data == 'cancel')
async def cancel_process_cb(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.reply("Хорошо, забыли.")
    await call.message.delete_reply_markup()
    await call.answer()


@dp.message(F.text == keyboards.bt_settings.text)
async def settings(msg: types.Message):
    await msg.answer("⚙ Давайте настроим...", reply_markup=keyboards.kb_settings)


@dp.message(F.text == keyboards.bt_back.text)
async def restore_keyboard(msg: types.Message):
    await msg.answer("👌 Хорошо, больше не настраиваем...", reply_markup=keyboards.kb_main)


@dp.message(F.text == keyboards.bt_mailing_config.text)
async def configure_mailing(msg: types.Message, state: FSMContext):
    if not await validate_user(msg.from_user.id):
        logging.info(f"user validation failed - id: {msg.from_user.id}, username: @{msg.from_user.username}")
        return

    logging.info(f"attempted configure mailing - id: {msg.from_user.id}, username: @{msg.from_user.username}")

    if db.get_mailing_time(msg.from_user.id):
        await cancel_mailing(msg, state)
        return

    await msg.answer("🔔 Хочешь подписаться на <b>рассылку</b> расписания?\n\n"
                     "Каждый день бот будет начинать рассылать <b>расписание на завтрашний день в 18:00</b>.\n"
                     "Рассылка может занять некоторое время, обычно около получаса. "
                     "Ты в любой момент сможешь как отписаться, так и подписаться снова.",
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[[keyboards.inline_bt_confirm], [keyboards.inline_bt_cancel]]))
    await state.set_state(states.Mailing.Subscribe)


@dp.callback_query(states.Mailing.Subscribe)
async def set_mailing(call: types.CallbackQuery, state: FSMContext):
    db.set_mailing_time(call.from_user.id, '18:00')
    await state.clear()
    await call.answer()

    logging.info(f"subscribed to mailing - id: {call.from_user.id}, username: @{call.from_user.username}")

    await call.message.edit_text(
        "🤖 Хорошо, в следующий раз, когда буду рассылать расписание, обязательно напишу и тебе!")


async def cancel_mailing(msg: types.Message, state: FSMContext):
    await msg.answer("🔕 Хочешь отписаться от <b>рассылки</b> расписания?\n\n"
                     "Рассылка <b>может занять некоторое время</b>, обычно около получаса. "
                     "Если ждать уже надоело и думаешь, что что-то пошло не так, можешь написать админу, "
                     "ссылка есть в описании бота.\n"
                     "Ты в любой момент сможешь как подписаться, так и отписаться снова.",
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[[keyboards.inline_bt_confirm], [keyboards.inline_bt_cancel]]))
    await state.set_state(states.Mailing.Unsubscribe)


async def stop_mailing(call: types.CallbackQuery, state: FSMContext):
    db.del_mailing_time(call.from_user.id)
    await state.clear()
    await call.answer()

    logging.info(f"unsubscribed from mailing - id: {call.from_user.id}, username: @{call.from_user.username}")

    await call.message.edit_text(
        "🤖 Хорошо, больше не буду автоматически присылать тебе расписание на завтра.")


@dp.callback_query(states.Mailing.Unsubscribe)
async def stop_mailing_from_config(call: types.CallbackQuery, state: FSMContext):
    await stop_mailing(call, state)
    

@dp.callback_query(F.data == keyboards.inline_bt_unsub.callback_data)
async def stop_mailing_from_message(call: types.CallbackQuery, state: FSMContext):
    await stop_mailing(call, state)


@dp.message(F.text == keyboards.bt_group_config.text)
async def start_group_config(msg: types.Message, state: FSMContext):
    groups = await open_groups_file()

    logging.info(f"{msg.from_user.id} (@{msg.from_user.username})")

    msg_text, inline_kb_numbers = await generate_kb_nums(groups)

    await msg.answer(f"<b>На клавиатуре ниже выберите цифру, соответствующую вашему факультету:</b>\n\n"
                     f"{msg_text}",
                     reply_markup=inline_kb_numbers)
    await state.set_state(states.UserData.Faculty)


@dp.callback_query(NumCallback.filter(), states.UserData.Faculty)
async def set_faculty(call: CallbackQuery, callback_data: NumCallback, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()
    faculty_name = list(groups.keys())[callback_data.num - 1]
    forms = groups[faculty_name]
    await state.update_data(faculty=faculty_name)

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {faculty_name}")

    msg_text, inline_kb_numbers = await generate_kb_nums(forms)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашей форме обучения:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers
                                 )
    await state.set_state(states.UserData.Form)


@dp.callback_query(NumCallback.filter(), states.UserData.Form)
async def set_form(call: CallbackQuery, callback_data: NumCallback, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()

    data = await state.get_data()
    faculty_name = data['faculty']
    form_name = list(groups[faculty_name].keys())[callback_data.num - 1]
    await state.update_data(form=form_name)

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {form_name}")

    steps = groups[faculty_name][form_name]

    msg_text, inline_kb_numbers = await generate_kb_nums(steps)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашей ступени обучения:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers
                                 )
    await state.set_state(states.UserData.Step)


@dp.callback_query(NumCallback.filter(), states.UserData.Step)
async def set_step(call: CallbackQuery, callback_data: NumCallback, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()
    
    data = await state.get_data()
    faculty_name = data['faculty']
    form_name = data['form']
    step_name = list(groups[faculty_name][form_name].keys())[callback_data.num - 1]
    await state.update_data(step=step_name)

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {step_name}")

    courses = groups[faculty_name][form_name][step_name]

    msg_text, inline_kb_numbers = await generate_kb_nums(courses)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашему году обучения:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers
                                 )
    await state.set_state(states.UserData.Course)


@dp.callback_query(NumCallback.filter(), states.UserData.Course)
async def set_course(call: CallbackQuery, callback_data: NumCallback, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()
    
    data = await state.get_data()
    faculty_name = data['faculty']
    form_name = data['form']
    step_name = data['step']
    course_name = list(groups[faculty_name][form_name][step_name].keys())[callback_data.num - 1]
    await state.update_data(course=course_name)

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {course_name}")

    groups = groups[faculty_name][form_name][step_name][course_name]

    msg_text, inline_kb_numbers = await generate_kb_nums(groups)

    await call.message.edit_text(f"<b>На клавиатуре ниже выберите цифру, "
                                 f"соответствующую вашей группе:</b>\n\n"
                                 f"{msg_text}",
                                 reply_markup=inline_kb_numbers
                                 )
    await state.set_state(states.UserData.Group)


@dp.callback_query(NumCallback.filter(), states.UserData.Group)
async def set_group(call: CallbackQuery, callback_data: NumCallback, state: FSMContext):
    await call.answer()

    groups = await open_groups_file()
    
    data = await state.get_data()
    faculty_name = data['faculty']
    form_name = data['form']
    step_name = data['step']
    course_name = data['course']
    group_name = list(groups[faculty_name][form_name][step_name][course_name].keys())[callback_data.num - 1]
    group_id = groups[faculty_name][form_name][step_name][course_name][group_name]
    await state.update_data(group_id=group_id)

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {group_name} ({group_id})")

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Без подгруппы', callback_data=NumCallback(num=0).pack()))
    builder.row(InlineKeyboardButton(text='1', callback_data=NumCallback(num=1).pack()),
                InlineKeyboardButton(text='2', callback_data=NumCallback(num=2).pack()))
    builder.row(keyboards.inline_bt_cancel)
    
    await call.message.edit_text("Если такая есть, выберите <b>номер подгруппы.</b> "
                                 "Если отсутствует, нажмите кнопку <b>\"Без подгруппы\"</b>.",
                                 reply_markup=builder.as_markup())
    await state.set_state(states.UserData.SubGroup)


@dp.callback_query(NumCallback.filter(), states.UserData.SubGroup)
async def set_subgroup(call: CallbackQuery, callback_data: NumCallback, state: FSMContext):
    await call.answer()

    data = await state.get_data()
    group_id = data['group_id']
    sub_group = int(callback_data.num)

    logging.info(f"{call.from_user.id} (@{call.from_user.username}) - {sub_group}")

    if sub_group not in range(3):
        logging.info(
            f"fail: {call.from_user.id} (@{call.from_user.username})")
        await call.message.edit_text("<b>Упс! Что-то пошло не так, пока мы устанавливали подгруппу...</b>\n"
                                     "Придется настроить заново 😓")
        await state.clear()
        return

    db.add_user(call.from_user.id, group_id, sub_group)

    await call.message.edit_text("<b>Хорошо, все готово!</b>\n"
                                 "Теперь можешь использовать кнопки, чтобы смотреть расписание!")
    await state.clear()
    logging.info(f"add: {call.from_user.id} (@{call.from_user.username})")
    await basic_handlers.get_help(call.message)
