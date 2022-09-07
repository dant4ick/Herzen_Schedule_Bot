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
        await msg.answer("Вы уверены, что хотите отправить это сообщение всем пользователям?",
                         reply_markup=InlineKeyboardMarkup().add(
                             keyboards.inline_bt_confirm, keyboards.inline_bt_cancel
                         ))
        await Broadcast.next()


@dp.callback_query_handler(text='confirm', state=Broadcast.Confirmation)
async def send_broadcast_message(call: CallbackQuery, state: FSMContext):
    if call.from_user.id == ADMIN_TELEGRAM_ID:
        await call.answer()
        await call.message.edit_text("Хорошо, отправляю...")
        async with state.proxy() as data:
            msg = data['message']
        await state.finish()

        for user_id in db.get_all_id():
            await broadcast_message(user_id[0], msg)
            await asyncio.sleep(.05)
