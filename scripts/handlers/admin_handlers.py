import asyncio

from aiogram import types
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery

from scripts.bot import dp, db

from config import ADMIN_TELEGRAM_ID
from scripts.handlers import keyboards
from scripts.states import Broadcast
from scripts.utils import broadcast_message


@dp.message_handler(commands=['admin'])
async def show_admin_menu(msg: Message):
    if msg.from_user.id == ADMIN_TELEGRAM_ID:
        await msg.answer("Привет, админ!", reply_markup=keyboards.kb_admin)


@dp.message_handler(filters.Text(contains='вернуть клавиатуру пользователя', ignore_case=True))
async def show_admin_menu(msg: Message):
    if msg.from_user.id == ADMIN_TELEGRAM_ID:
        await msg.answer("Пока, админ!", reply_markup=keyboards.kb_main)


@dp.message_handler(filters.Text(contains='отправить сообщение всем', ignore_case=True))
async def get_broadcast_message(msg: types.Message):
    if msg.from_user.id == ADMIN_TELEGRAM_ID:
        await msg.answer("Пришлите сообщение, которое нужно разослать всем пользователям...")
        await Broadcast.Message.set()


@dp.message_handler(state=Broadcast.Message, content_types=types.ContentType.ANY)
async def confirm_broadcast_message(msg: types.Message, state: FSMContext):
    if msg.from_user.id == ADMIN_TELEGRAM_ID:
        async with state.proxy() as data:
            data['message'] = msg

        await msg.forward(ADMIN_TELEGRAM_ID)
        await msg.answer("Вы хотите переслать сообщение или отправить копию от имени бота?",
                         reply_markup=InlineKeyboardMarkup().add(
                             keyboards.InlineKeyboardButton("Переслать", callback_data="forward"),
                             keyboards.InlineKeyboardButton("Отправить копию", callback_data="copy"),
                         ).row(keyboards.inline_bt_cancel))
        await Broadcast.next()


@dp.callback_query_handler(state=Broadcast.MessageType)
async def send_broadcast_message(call: CallbackQuery, state: FSMContext):
    if call.from_user.id == ADMIN_TELEGRAM_ID:
        await call.answer()
        async with state.proxy() as data:
            msg = data['message']
        msg_type = call.data
        await state.finish()

        all_id = db.get_all_id()
        all_id.remove((ADMIN_TELEGRAM_ID,))

        max_counter = len(all_id)
        quarters = [round(max_counter * 0.25),
                    round(max_counter * 0.5),
                    round(max_counter * 0.75),
                    max_counter
                    ]
        msg_counter = 0

        await call.message.edit_text(f"Хорошо, отправляю {max_counter} сообщений...")
        for user_id in all_id:
            await broadcast_message(user_id[0], msg, msg_type)
            msg_counter += 1
            if msg_counter in quarters:
                await asyncio.sleep(.5)
                quarter = quarters.index(msg_counter) + 1
                await call.message.edit_text(f"Отправлено {msg_counter} из {max_counter} "
                                             f"<code>[{'#' * quarter}{'-' * (4 - quarter)}]</code>")
            await asyncio.sleep(.1)
